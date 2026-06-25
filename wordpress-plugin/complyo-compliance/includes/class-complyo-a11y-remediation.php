<?php
/**
 * Complyo Accessibility – Serverseitige Alt-Text-Remediation
 * =========================================================
 * Holt freigegebene KI-Alt-Texte vom Complyo-Backend und wendet sie
 * AN DER QUELLE an (Attachment-Meta `_wp_attachment_image_alt`), nicht nur
 * als Client-Overlay. Zusätzlich Render-Fallbacks für Bilder ohne Alt:
 *  - wp_get_attachment_image_attributes (Attachment-Bilder)
 *  - the_content (inline <img> via DOMDocument)
 *
 * Quelle der Fixes: GET {API}/api/accessibility/alt-text-fixes?site_id=…&approved_only=true
 * (kanonischer Endpoint; nur Status "approved" wird ausgeliefert).
 *
 * @package complyo-compliance
 */

if (!defined('ABSPATH')) {
    exit;
}

class Complyo_A11y_Remediation {

    const OPTION_MAP       = 'complyo_a11y_alt_map';   // [normalisierter_dateiname => alt-text]
    const OPTION_LAST_SYNC = 'complyo_a11y_last_sync'; // unix timestamp
    const CRON_HOOK        = 'complyo_a11y_sync_event';

    private static $instance = null;

    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    private function __construct() {
        // Cron-Callback immer registrieren, damit ein geplanter Lauf nicht ins Leere geht.
        add_action(self::CRON_HOOK, array($this, 'sync_fixes'));
        // Manueller Sync aus dem Admin.
        add_action('admin_post_complyo_a11y_sync', array($this, 'handle_admin_sync'));

        if (!$this->is_enabled()) {
            // Bei Deaktivierung geplanten Lauf entfernen.
            $this->maybe_unschedule();
            return;
        }

        add_action('init', array($this, 'maybe_schedule'));

        // Render-Fallbacks (nur Frontend).
        add_filter('wp_get_attachment_image_attributes', array($this, 'filter_attachment_attributes'), 20, 2);
        add_filter('the_content', array($this, 'filter_content_images'), 20);
    }

    private function is_enabled() {
        return get_option(COMPLYO_OPTION_A11Y_SOURCE_FIX, '0') === '1';
    }

    private function get_site_id() {
        $id = get_option(COMPLYO_OPTION_SITE_ID, '');
        if (!empty($id)) {
            return $id;
        }
        $domain = parse_url(home_url(), PHP_URL_HOST);
        $domain = preg_replace('/^www\./', '', (string) $domain);
        return sanitize_key(str_replace('.', '-', strtolower($domain)));
    }

    // =========================================================================
    // Cron-Planung
    // =========================================================================

    public function maybe_schedule() {
        if (!wp_next_scheduled(self::CRON_HOOK)) {
            wp_schedule_event(time() + 60, 'hourly', self::CRON_HOOK);
        }
    }

    private function maybe_unschedule() {
        $ts = wp_next_scheduled(self::CRON_HOOK);
        if ($ts) {
            wp_unschedule_event($ts, self::CRON_HOOK);
        }
    }

    public function handle_admin_sync() {
        if (!current_user_can('manage_options')) {
            wp_die(esc_html__('Keine Berechtigung.', 'complyo-compliance'));
        }
        check_admin_referer('complyo_a11y_sync');
        $count = $this->sync_fixes();
        wp_safe_redirect(add_query_arg(
            array('page' => 'complyo-compliance', 'complyo_a11y_synced' => (int) $count),
            admin_url('options-general.php')
        ));
        exit;
    }

    // =========================================================================
    // Sync: Fixes holen, Map cachen, an der Quelle persistieren
    // =========================================================================

    /**
     * @return int Anzahl der gespeicherten/aktualisierten Quell-Alt-Texte.
     */
    public function sync_fixes() {
        $site_id = $this->get_site_id();
        if (empty($site_id)) {
            return 0;
        }

        $url = trailingslashit(COMPLYO_API_BASE)
            . 'api/accessibility/alt-text-fixes?site_id=' . rawurlencode($site_id) . '&approved_only=true';

        $res = wp_remote_get($url, array('timeout' => 15));
        if (is_wp_error($res) || (int) wp_remote_retrieve_response_code($res) !== 200) {
            return 0;
        }

        $body = json_decode(wp_remote_retrieve_body($res), true);
        if (!is_array($body) || empty($body['fixes']) || !is_array($body['fixes'])) {
            // Leeres Ergebnis ist gültig (nichts freigegeben) – Map leeren, Zeitstempel setzen.
            update_option(self::OPTION_MAP, array());
            update_option(self::OPTION_LAST_SYNC, time());
            return 0;
        }

        $map = array();
        $persisted = 0;

        foreach ($body['fixes'] as $fix) {
            $alt = $this->extract_alt($fix);
            $src = isset($fix['image_src']) ? (string) $fix['image_src'] : '';
            $fname = isset($fix['image_filename']) ? (string) $fix['image_filename'] : '';
            if ($alt === '' || ($src === '' && $fname === '')) {
                continue;
            }

            // Render-Map nach normalisiertem Dateinamen.
            foreach (array($fname, $src) as $candidate) {
                $key = $this->normalize_filename($candidate);
                if ($key !== '') {
                    $map[$key] = $alt;
                }
            }

            // QUELL-PERSISTENZ: passendes Attachment finden und Alt setzen, falls leer.
            if ($src !== '') {
                $persisted += $this->persist_to_attachment($src, $alt);
            }
        }

        update_option(self::OPTION_MAP, $map);
        update_option(self::OPTION_LAST_SYNC, time());
        return $persisted;
    }

    private function extract_alt($fix) {
        if (!is_array($fix)) {
            return '';
        }
        foreach (array('suggested_alt', 'alt_text', 'generated_alt') as $k) {
            if (!empty($fix[$k])) {
                return trim(sanitize_text_field($fix[$k]));
            }
        }
        return '';
    }

    /**
     * Setzt `_wp_attachment_image_alt` für das zur URL passende Attachment,
     * sofern dort noch kein Alt-Text hinterlegt ist (überschreibt nichts Manuelles).
     *
     * @return int 1 wenn gesetzt, sonst 0.
     */
    private function persist_to_attachment($image_src, $alt) {
        // Vollständige URL → Attachment-ID. Relative Pfade auf Home-URL beziehen.
        $url = $image_src;
        if (strpos($url, 'http') !== 0) {
            $url = home_url('/') . ltrim($image_src, '/');
        }
        $attachment_id = attachment_url_to_postid($url);
        if (!$attachment_id) {
            return 0;
        }
        $existing = get_post_meta($attachment_id, '_wp_attachment_image_alt', true);
        if (!empty($existing)) {
            return 0; // Manuell/vorhandenen Alt-Text nicht überschreiben.
        }
        update_post_meta($attachment_id, '_wp_attachment_image_alt', $alt);
        return 1;
    }

    // =========================================================================
    // Render-Fallbacks
    // =========================================================================

    public function filter_attachment_attributes($attr, $attachment) {
        if (!empty($attr['alt'])) {
            return $attr;
        }
        $map = $this->get_map();
        if (empty($map)) {
            return $attr;
        }
        $src = isset($attr['src']) ? $attr['src'] : '';
        $key = $this->normalize_filename($src);
        if ($key !== '' && isset($map[$key])) {
            $attr['alt'] = $map[$key];
        }
        return $attr;
    }

    public function filter_content_images($content) {
        if (is_admin() || is_feed() || empty($content) || strpos($content, '<img') === false) {
            return $content;
        }
        $map = $this->get_map();
        if (empty($map)) {
            return $content;
        }

        $changed = false;
        $previous = libxml_use_internal_errors(true);
        $dom = new DOMDocument();
        // utf-8 erzwingen, kein impliziertes <html>/<body>, keine DTD.
        $ok = $dom->loadHTML(
            '<?xml encoding="utf-8"?><div id="complyo-a11y-root">' . $content . '</div>',
            LIBXML_HTML_NOIMPLIED | LIBXML_HTML_NODEFDTD
        );
        if (!$ok) {
            libxml_clear_errors();
            libxml_use_internal_errors($previous);
            return $content;
        }

        foreach ($dom->getElementsByTagName('img') as $img) {
            $current = $img->getAttribute('alt');
            if ($current !== '') {
                continue; // vorhandenen Alt nicht anfassen.
            }
            $src = $img->getAttribute('src');
            if ($src === '') {
                $src = $img->getAttribute('data-src');
            }
            $key = $this->normalize_filename($src);
            if ($key !== '' && isset($map[$key])) {
                $img->setAttribute('alt', $map[$key]);
                $changed = true;
            }
        }

        if (!$changed) {
            libxml_clear_errors();
            libxml_use_internal_errors($previous);
            return $content;
        }

        // Inneres des Wrapper-Divs zurückgeben (ohne Wrapper). Unter NOIMPLIED ist
        // unser <div> das documentElement; getElementById ist nach loadHTML unzuverlässig.
        $root = $dom->documentElement;
        $html = '';
        if ($root && strtolower($root->nodeName) === 'div') {
            foreach ($root->childNodes as $child) {
                $html .= $dom->saveHTML($child);
            }
        }
        libxml_clear_errors();
        libxml_use_internal_errors($previous);

        return $html !== '' ? $html : $content;
    }

    // =========================================================================
    // Helper
    // =========================================================================

    private function get_map() {
        $map = get_option(self::OPTION_MAP, array());
        return is_array($map) ? $map : array();
    }

    /**
     * Normalisiert einen Pfad/eine URL auf den Basis-Dateinamen (klein),
     * inklusive Entfernung der WP-Größensuffixe (z. B. -300x200).
     */
    private function normalize_filename($path) {
        if (!is_string($path) || $path === '') {
            return '';
        }
        $base = strtolower(basename(parse_url($path, PHP_URL_PATH) ?: $path));
        // Query/Fragment-Reste entfernen.
        $base = preg_replace('/[?#].*$/', '', $base);
        // WP-Größensuffix vor der Endung entfernen: name-300x200.jpg -> name.jpg
        $base = preg_replace('/-\d+x\d+(\.[a-z0-9]+)$/i', '$1', $base);
        return $base;
    }
}
