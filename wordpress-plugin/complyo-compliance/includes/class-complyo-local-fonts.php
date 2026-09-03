<?php
/**
 * Complyo – Google Fonts lokal laden (DSGVO / LG München 3 O 17493/20)
 *
 * Lädt extern eingebundene Google Fonts (fonts.googleapis.com / fonts.gstatic.com)
 * auf den eigenen Server und schreibt die Seitenausgabe so um, dass KEIN Request
 * an Google mehr ausgeht – auch nicht vor dem Cookie-Consent. Damit ist der
 * statische Font-Fall hart geschlossen (der Client-Blocker kann den Preload-
 * Scanner nicht überholen; das Self-Hosting schon).
 *
 * Ablauf:
 *  1. Verarbeitung (Download + lokales CSS) läuft NIE im Besucher-Request,
 *     sondern per Admin-Button ("Jetzt lokalisieren") oder Hintergrund-Cron.
 *  2. Im Frontend werden bekannte fonts.googleapis.com-URLs per Output-Buffer
 *     auf die lokale Kopie umgeschrieben; gstatic-Preconnect/Preload entfernt.
 *  3. Neu entdeckte (noch nicht lokalisierte) URLs werden gequeued und vom Cron
 *     verarbeitet – der Besucher-Request bleibt unblockierend.
 *
 * @package Complyo_Compliance
 */

if (!defined('ABSPATH')) {
    exit;
}

class Complyo_Local_Fonts {

    const OPTION_ENABLE  = 'complyo_enable_local_fonts';
    const OPTION_MAP     = 'complyo_local_fonts_map';     // [ googleapis-URL => lokale CSS-URL ]
    const OPTION_PENDING = 'complyo_local_fonts_pending'; // [ googleapis-URL, … ]
    const CRON_HOOK      = 'complyo_process_local_fonts';
    const DIR_NAME       = 'complyo-fonts';

    private static $instance = null;

    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    private function __construct() {
        // Cron-Handler + Admin-Aktion immer registrieren (auch bei deaktiviert,
        // damit ein laufender Cron-Job zu Ende verarbeiten kann).
        add_action(self::CRON_HOOK, array($this, 'process_pending'));
        add_action('admin_post_complyo_localize_fonts', array($this, 'handle_admin_localize'));

        if (get_option(self::OPTION_ENABLE, '0') !== '1') {
            return;
        }

        // Frontend-Rewrites
        if (!is_admin()) {
            add_action('wp_enqueue_scripts', array($this, 'rewrite_enqueued_fonts'), 100);
            add_filter('style_loader_tag',   array($this, 'filter_style_tag'), 10, 4);
            add_action('template_redirect',  array($this, 'start_output_buffer'), 1);
        }
    }

    // =========================================================================
    // Pfade / Helpers
    // =========================================================================

    private function base_dir() {
        $up = wp_upload_dir();
        return trailingslashit($up['basedir']) . self::DIR_NAME;
    }

    private function base_url() {
        $up = wp_upload_dir();
        return trailingslashit($up['baseurl']) . self::DIR_NAME;
    }

    /** Ist die URL eine Google-Fonts-Stylesheet-URL? */
    private function is_google_fonts_css($url) {
        if (!$url) {
            return false;
        }
        $host = wp_parse_url($url, PHP_URL_HOST);
        return $host === 'fonts.googleapis.com';
    }

    /** Liefert die lokale CSS-URL für eine googleapis-URL, falls bereits lokalisiert. */
    private function local_css_for($url) {
        $map = get_option(self::OPTION_MAP, array());
        return isset($map[$url]) ? $map[$url] : null;
    }

    // =========================================================================
    // Frontend: Umschreiben
    // =========================================================================

    /** Output-Buffer starten (nur normale HTML-Frontend-Requests). */
    public function start_output_buffer() {
        if (is_admin() || is_feed() || (defined('REST_REQUEST') && REST_REQUEST) || wp_doing_ajax()) {
            return;
        }
        ob_start(array($this, 'rewrite_html'));
    }

    /**
     * Schreibt die fertige HTML-Ausgabe um:
     *  - bekannte fonts.googleapis.com-Stylesheets → lokale Kopie
     *  - gstatic/googleapis Preconnect/DNS-Prefetch/Preload entfernen
     *  - unbekannte googleapis-URLs zur Verarbeitung einreihen (non-blocking)
     */
    public function rewrite_html($html) {
        if (!is_string($html) || $html === '') {
            return $html;
        }

        $map      = get_option(self::OPTION_MAP, array());
        $newly    = array();

        // 1) <link rel="stylesheet" href="https://fonts.googleapis.com/…">
        $html = preg_replace_callback(
            '#<link\b[^>]*href=(["\'])(https?://fonts\.googleapis\.com/[^"\']+)\1[^>]*>#i',
            function ($m) use ($map, &$newly) {
                $url = html_entity_decode($m[2]);
                if (isset($map[$url])) {
                    // href auf lokale Kopie umbiegen, media-Reste belassen
                    return str_replace($m[2], esc_url($map[$url]), $m[0]);
                }
                $newly[$url] = true;
                return $m[0]; // unverändert lassen, bis lokalisiert
            },
            $html
        );

        // 2) Preconnect / DNS-Prefetch / Preload auf Google-Font-Hosts entfernen
        $html = preg_replace(
            '#<link\b[^>]*(?:fonts\.gstatic\.com|fonts\.googleapis\.com)[^>]*(?:rel=(["\'])(?:preconnect|dns-prefetch|preload)\1|as=(["\'])font\2)[^>]*>#i',
            '',
            $html
        );
        // … und die umgekehrte Attribut-Reihenfolge (rel zuerst)
        $html = preg_replace(
            '#<link\b[^>]*rel=(["\'])(?:preconnect|dns-prefetch|preload)\1[^>]*(?:fonts\.gstatic\.com|fonts\.googleapis\.com)[^>]*>#i',
            '',
            $html
        );

        if (!empty($newly)) {
            $this->queue_urls(array_keys($newly));
        }

        return $html;
    }

    /**
     * Enqueued Google-Fonts-Handles auf lokale Kopie umbiegen bzw. einreihen.
     * Greift VOR der HTML-Ausgabe und ist die saubere Variante für korrekt
     * via wp_enqueue_style() eingebundene Fonts.
     */
    public function rewrite_enqueued_fonts() {
        if (!isset($GLOBALS['wp_styles']) || !($GLOBALS['wp_styles'] instanceof WP_Styles)) {
            return;
        }
        $styles = $GLOBALS['wp_styles'];
        $queue  = array();

        foreach ($styles->registered as $handle => $style) {
            $src = isset($style->src) ? $style->src : '';
            if (!$this->is_google_fonts_css($src)) {
                continue;
            }
            $local = $this->local_css_for($src);
            if ($local) {
                $styles->registered[$handle]->src = $local;
            } else {
                $queue[] = $src;
            }
        }

        if (!empty($queue)) {
            $this->queue_urls($queue);
        }
    }

    /** Fallback: rohe <link>-Tags aus style_loader_tag umschreiben. */
    public function filter_style_tag($tag, $handle, $href, $media) {
        if (!$this->is_google_fonts_css($href)) {
            return $tag;
        }
        $local = $this->local_css_for($href);
        if ($local) {
            return str_replace($href, esc_url($local), $tag);
        }
        $this->queue_urls(array($href));
        return $tag;
    }

    // =========================================================================
    // Queue / Cron
    // =========================================================================

    private function queue_urls($urls) {
        $pending = get_option(self::OPTION_PENDING, array());
        $changed = false;
        foreach ($urls as $url) {
            if ($this->is_google_fonts_css($url) && !in_array($url, $pending, true)) {
                $pending[] = $url;
                $changed   = true;
            }
        }
        if ($changed) {
            update_option(self::OPTION_PENDING, array_values(array_unique($pending)), false);
            if (!wp_next_scheduled(self::CRON_HOOK)) {
                wp_schedule_single_event(time() + 30, self::CRON_HOOK);
            }
        }
    }

    /** Cron: alle eingereihten URLs verarbeiten. */
    public function process_pending() {
        $pending = get_option(self::OPTION_PENDING, array());
        if (empty($pending)) {
            return;
        }
        foreach ($pending as $url) {
            $this->process_url($url);
        }
        update_option(self::OPTION_PENDING, array(), false);
    }

    // =========================================================================
    // Download + Lokalisierung
    // =========================================================================

    /**
     * Liest die Startseite, findet Google-Fonts-URLs und verarbeitet sie sofort.
     * Wird vom Admin-Button "Jetzt lokalisieren" genutzt.
     *
     * @return array{found:int, localized:int, errors:int}
     */
    public function process_site() {
        $result = array('found' => 0, 'localized' => 0, 'errors' => 0);

        $resp = wp_remote_get(home_url('/'), array(
            'timeout'    => 20,
            'user-agent' => $this->desktop_ua(),
        ));
        if (is_wp_error($resp)) {
            $result['errors']++;
            return $result;
        }
        $html = wp_remote_retrieve_body($resp);
        if (!$html) {
            return $result;
        }

        if (preg_match_all('#https?://fonts\.googleapis\.com/[^"\'\s>]+#i', $html, $m)) {
            $urls = array_unique(array_map('html_entity_decode', $m[0]));
            foreach ($urls as $url) {
                $result['found']++;
                if ($this->process_url($url)) {
                    $result['localized']++;
                } else {
                    $result['errors']++;
                }
            }
        }
        return $result;
    }

    /**
     * Lädt EIN Google-Fonts-CSS + zugehörige Font-Dateien lokal, schreibt das
     * CSS auf lokale URLs um und speichert es. Aktualisiert die URL→lokal-Map.
     *
     * @return bool Erfolg
     */
    public function process_url($url) {
        if (!$this->is_google_fonts_css($url)) {
            return false;
        }

        // Mit Desktop-User-Agent anfragen → Google liefert woff2-@font-face.
        $resp = wp_remote_get($url, array(
            'timeout'    => 20,
            'user-agent' => $this->desktop_ua(),
        ));
        if (is_wp_error($resp) || wp_remote_retrieve_response_code($resp) !== 200) {
            return false;
        }
        $css = wp_remote_retrieve_body($resp);
        if (!$css) {
            return false;
        }

        if (!$this->ensure_dirs()) {
            return false;
        }

        $fonts_dir = trailingslashit($this->base_dir()) . 'files';
        $fonts_url = trailingslashit($this->base_url()) . 'files';

        // Alle url(...)-Verweise auf gstatic-Fontdateien herunterladen + ersetzen.
        $css = preg_replace_callback(
            '#url\(\s*([\'"]?)(https?://fonts\.gstatic\.com/[^\)\'"\s]+)\1\s*\)#i',
            function ($m) use ($fonts_dir, $fonts_url) {
                $remote = $m[2];
                $ext    = pathinfo(wp_parse_url($remote, PHP_URL_PATH), PATHINFO_EXTENSION);
                $ext    = preg_replace('/[^a-z0-9]/i', '', $ext) ?: 'woff2';
                $name   = md5($remote) . '.' . $ext;
                $target = trailingslashit($fonts_dir) . $name;

                if (!file_exists($target)) {
                    $fr = wp_remote_get($remote, array('timeout' => 20, 'user-agent' => $this->desktop_ua()));
                    if (is_wp_error($fr) || wp_remote_retrieve_response_code($fr) !== 200) {
                        return $m[0]; // Original belassen, wenn Download scheitert
                    }
                    $bin = wp_remote_retrieve_body($fr);
                    if (!$bin || !$this->write_file($target, $bin)) {
                        return $m[0];
                    }
                }
                return "url('" . trailingslashit($fonts_url) . $name . "')";
            },
            $css
        );

        // font-display: swap ergänzen, wenn nicht vorhanden (Layout-Stabilität).
        if (strpos($css, 'font-display') === false) {
            $css = preg_replace('/@font-face\s*\{/i', "@font-face{font-display:swap;", $css);
        }

        $css_dir  = trailingslashit($this->base_dir()) . 'css';
        $css_name = md5($url) . '.css';
        $css_path = trailingslashit($css_dir) . $css_name;
        if (!$this->write_file($css_path, $css)) {
            return false;
        }

        $local_url = trailingslashit($this->base_url()) . 'css/' . $css_name;
        $map       = get_option(self::OPTION_MAP, array());
        $map[$url] = $local_url;
        update_option(self::OPTION_MAP, $map, false);

        return true;
    }

    // =========================================================================
    // Admin-Aktion
    // =========================================================================

    public function handle_admin_localize() {
        if (!current_user_can('manage_options')) {
            wp_die(esc_html__('Keine Berechtigung.', 'complyo-compliance'));
        }
        check_admin_referer('complyo_localize_fonts');

        $res = $this->process_site();

        $redirect = add_query_arg(
            array(
                'page'             => 'complyo-compliance',
                'complyo_fonts'    => '1',
                'cf_found'         => (int) $res['found'],
                'cf_localized'     => (int) $res['localized'],
                'cf_errors'        => (int) $res['errors'],
            ),
            admin_url('options-general.php')
        );
        wp_safe_redirect($redirect);
        exit;
    }

    /** Anzahl aktuell lokalisierter Font-Stylesheets (für die Admin-Anzeige). */
    public function localized_count() {
        $map = get_option(self::OPTION_MAP, array());
        return is_array($map) ? count($map) : 0;
    }

    /** Alle lokalen Font-Dateien + Map entfernen (z.B. beim Zurücksetzen). */
    public function purge() {
        update_option(self::OPTION_MAP, array(), false);
        update_option(self::OPTION_PENDING, array(), false);
    }

    // =========================================================================
    // Dateisystem
    // =========================================================================

    private function ensure_dirs() {
        $dirs = array(
            $this->base_dir(),
            trailingslashit($this->base_dir()) . 'css',
            trailingslashit($this->base_dir()) . 'files',
        );
        foreach ($dirs as $d) {
            if (!wp_mkdir_p($d)) {
                return false;
            }
        }
        // Verzeichnis-Listing verhindern.
        $index = trailingslashit($this->base_dir()) . 'index.html';
        if (!file_exists($index)) {
            $this->write_file($index, '');
        }
        return true;
    }

    private function write_file($path, $contents) {
        // Bevorzugt WP_Filesystem, Fallback file_put_contents.
        global $wp_filesystem;
        if (empty($wp_filesystem)) {
            require_once ABSPATH . 'wp-admin/includes/file.php';
            WP_Filesystem();
        }
        if ($wp_filesystem) {
            return $wp_filesystem->put_contents($path, $contents, FS_CHMOD_FILE);
        }
        return false !== @file_put_contents($path, $contents);
    }

    private function desktop_ua() {
        return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
             . '(KHTML, like Gecko) Chrome/124.0 Safari/537.36';
    }
}
