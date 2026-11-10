<?php
/**
 * Complyo – Server-seitiges Inline-Script-Blocking
 *
 * Inline-Tracking-Snippets (Google Analytics/gtag, Meta Pixel, Hotjar, Matomo,
 * LinkedIn, TikTok, Pinterest, Bing UET, Clarity …) führen JS direkt im Markup
 * aus. Client-seitig lassen sie sich NICHT zuverlässig stoppen, weil sie beim
 * Parsen sofort laufen. Deshalb neutralisiert dieses Modul sie bereits in der
 * Server-Ausgabe: <script>…</script>  →  <script type="text/plain"
 * data-complyo-consent="<kategorie>" data-complyo-inline="1">…</script>.
 *
 * Der Complyo-Blocker im Browser führt sie nach erteiltem Consent wieder aus
 * (public/cookie-blocker.js, releaseScript).
 *
 * Seit 2.7.0 neutralisiert dieses Modul auch EXTERNE Tracker im Markup:
 * <script src>, <iframe src> (YouTube, Vimeo, Maps …) und Google-Fonts-<link>.
 * Grund (gemessen 09.11.2026, reinhardt.coffee): Der Vorlade-Scanner des Browsers
 * holt statische <script src>/<link href> schon, bevor irgendein Skript sie anfassen
 * kann. Ein Blocker im Browser kann das nicht verhindern; nur das Markup ohne
 * src/href kann es. Neutralisiert wird nach dem Muster
 *   <script type="text/plain" data-complyo-consent="<kategorie>" data-complyo-src="<url>">
 * Der Blocker im Browser gibt sie nach der Einwilligung frei (auch bei
 * wiederkehrenden Besuchern, die schon eingewilligt haben).
 *
 * @package Complyo_Compliance
 */

if (!defined('ABSPATH')) {
    exit;
}

class Complyo_Inline_Blocker {

    const OPTION_ENABLE = 'complyo_enable_inline_blocker';

    private static $instance = null;

    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    private function __construct() {
        if (get_option(self::OPTION_ENABLE, '0') !== '1') {
            return;
        }
        if (!is_admin()) {
            // Prioritaet 0: Dieser Puffer wird VOR dem der lokalen Schriften geoeffnet und damit
            // NACH ihm geleert. Erst wenn Complyo_Local_Fonts bekannte Google-Fonts-<link>s auf die
            // lokale Kopie gebogen hat, neutralisieren wir, was uebrig bleibt.
            add_action('template_redirect', array($this, 'start_buffer'), 0);
        }
    }

    /**
     * Inline-Tracker-Signaturen je Kategorie. Bewusst kuratiert: nur eindeutige
     * Tracker, um legitimes Inline-JS nicht zu beschädigen. Über den Filter
     * 'complyo_inline_patterns' erweiterbar.
     */
    private function patterns() {
        $patterns = array(
            'analytics' => array(
                '/\bgtag\s*\(/i',
                '/\bga\s*\(\s*[\'"]create/i',
                '/GoogleAnalyticsObject/i',
                '/dataLayer\s*\.\s*push/i',
                '/googletagmanager\.com\/gtm/i',
                '/\b_gaq\b/i',
                '/\b_paq\b/i',
                '/Matomo|piwik/i',
                '/hjid|_hjSettings|static\.hotjar\.com/i',
                '/clarity\s*\(|clarity\.ms/i',
            ),
            'marketing' => array(
                '/\bfbq\s*\(|connect\.facebook\.net|_fbq\b/i',
                '/_linkedin_partner_id|snap\.licdn\.com/i',
                '/\bttq\b|TiktokAnalyticsObject|analytics\.tiktok\.com/i',
                '/\bpintrk\s*\(/i',
                '/\buetq\b|bat\.bing\.com/i',
                '/\bsnaptr\s*\(/i',
            ),
        );
        return apply_filters('complyo_inline_patterns', $patterns);
    }

    /**
     * Externe Ziele, die vor der Einwilligung nicht abgerufen werden duerfen, je Kategorie.
     * Muster wie in public/cookie-blocker.js (SCRIPT_RULES/IFRAME_RULES). Ueber die Filter
     * 'complyo_external_script_patterns' und 'complyo_external_iframe_patterns' erweiterbar.
     */
    private function external_script_patterns() {
        $p = array(
            'analytics' => array(
                '#googletagmanager\.com/(gtag|gtm)#i',
                '#google-analytics\.com#i',
                '#static\.hotjar\.com#i',
                '#matomo\.js|piwik\.js#i',
                '#plausible\.io#i',
                '#clarity\.ms#i',
            ),
            'marketing' => array(
                '#connect\.facebook\.net#i',
                '#googleadservices\.com#i',
                '#doubleclick\.net#i',
                '#snap\.licdn\.com#i',
                '#analytics\.tiktok\.com#i',
                '#platform\.twitter\.com#i',
                '#youtube(-nocookie)?\.com/(iframe_api|player_api)#i',
                '#s\.ytimg\.com/yts/#i',
                '#www-widgetapi\.js#i',
                '#player\.vimeo\.com/api/#i',
            ),
            'functional' => array(
                '#widget\.intercom\.io#i',
                '#static\.zdassets\.com#i',
                '#embed\.tawk\.to#i',
                '#client\.crisp\.chat#i',
            ),
        );
        return apply_filters('complyo_external_script_patterns', $p);
    }

    private function external_iframe_patterns() {
        $p = array(
            'marketing' => array(
                '#youtube(-nocookie)?\.com/embed#i',
                '#player\.vimeo\.com#i',
                '#instagram\.com/embed#i',
                '#platform\.twitter\.com|twitter\.com/widgets#i',
            ),
            'functional' => array(
                '#google\.com/maps/embed#i',
            ),
        );
        return apply_filters('complyo_external_iframe_patterns', $p);
    }

    private function category_for($url, $patterns) {
        foreach (array('analytics', 'marketing', 'functional') as $cat) {
            if (empty($patterns[$cat])) { continue; }
            foreach ($patterns[$cat] as $re) {
                if (preg_match($re, $url)) { return $cat; }
            }
        }
        return null;
    }

    /** Page-Builder-Editoren und Vorschauen nicht anfassen. */
    private function is_editor_request() {
        foreach (array('vc_editable', 'elementor-preview', 'et_fb', 'fl_builder', 'brizy-edit', 'ct_builder') as $k) {
            if (isset($_GET[$k])) { return true; }
        }
        return function_exists('is_customize_preview') && is_customize_preview();
    }

    public function start_buffer() {
        if (is_admin() || is_feed() || (defined('REST_REQUEST') && REST_REQUEST) || wp_doing_ajax()
            || $this->is_editor_request()) {
            return;
        }
        ob_start(array($this, 'rewrite'));
    }

    /**
     * Externe Ziele neutralisieren: script src, iframe src und Google-Fonts-link.
     */
    private function rewrite_external($html) {
        $script_pat = $this->external_script_patterns();
        $iframe_pat = $this->external_iframe_patterns();

        // <script src="…"></script>
        $html = preg_replace_callback(
            '#<script\b([^>]*?)(?<![\w-])src\s*=\s*(["\'])([^"\']+)\2([^>]*)>(\s*)</script>#is',
            function ($m) use ($script_pat) {
                $url = html_entity_decode($m[3]);
                $cat = $this->category_for($url, $script_pat);
                if (!$cat) { return $m[0]; }
                $attrs = trim($m[1] . ' ' . $m[4]);
                $attrs = trim(preg_replace('/\btype\s*=\s*(["\']).*?\1/i', '', $attrs));
                return '<script type="text/plain" data-complyo-consent="' . esc_attr($cat) . '"'
                     . ' data-complyo-src="' . esc_attr($url) . '" data-complyo-blocked="true"'
                     . ($attrs !== '' ? ' ' . $attrs : '') . '></script>';
            },
            $html
        );

        // <iframe src="…">
        $html = preg_replace_callback(
            '#<iframe\b([^>]*?)(?<![\w-])src\s*=\s*(["\'])([^"\']+)\2([^>]*)>#is',
            function ($m) use ($iframe_pat) {
                $url = html_entity_decode($m[3]);
                $cat = $this->category_for($url, $iframe_pat);
                if (!$cat) { return $m[0]; }
                $attrs = trim($m[1] . ' ' . $m[4]);
                return '<iframe data-complyo-consent="' . esc_attr($cat) . '"'
                     . ' data-complyo-src="' . esc_attr($url) . '" data-complyo-blocked="true"'
                     . ($attrs !== '' ? ' ' . $attrs : '') . '>';
            },
            $html
        );

        // <link …href="//fonts.googleapis.com/…"> (nur, was Complyo_Local_Fonts nicht lokalisiert hat),
        // und Preconnect/Preload auf die Font-Hosts. Freigabe ueber die funktionale Einwilligung.
        $html = preg_replace_callback(
            '#<link\b([^>]*?)(?<![\w-])href\s*=\s*(["\'])((?:https?:)?//(?:fonts\.googleapis\.com|fonts\.gstatic\.com)[^"\']*)\2([^>]*)>#is',
            function ($m) {
                $url   = html_entity_decode($m[3]);
                $attrs = trim($m[1] . ' ' . $m[4]);
                $rel   = '';
                if (preg_match('/\brel\s*=\s*(["\'])(.*?)\1/i', $attrs, $rm)) { $rel = $rm[2]; }
                $attrs = trim(preg_replace('/\bmedia\s*=\s*(["\']).*?\1/i', '', $attrs));
                return '<link data-complyo-consent="functional" data-complyo-href="' . esc_attr($url) . '"'
                     . ' data-complyo-rel="' . esc_attr($rel) . '" data-complyo-blocked="true" media="not all"'
                     . ($attrs !== '' ? ' ' . $attrs : '') . '>';
            },
            $html
        );

        return $html;
    }

    /**
     * Findet Inline-<script>-Blöcke und neutralisiert Tracker.
     */
    public function rewrite($html) {
        if (!is_string($html) || $html === '') {
            return $html;
        }
        $html = $this->rewrite_external($html);
        if (stripos($html, '<script') === false) {
            return $html;
        }
        $patterns = $this->patterns();

        return preg_replace_callback(
            '#<script\b([^>]*)>(.*?)</script>#is',
            function ($m) use ($patterns) {
                $attrs = $m[1];
                $body  = $m[2];

                // Externe Scripts (src) → client-seitig behandelt, hier ignorieren.
                if (preg_match('/\bsrc\s*=/i', $attrs)) {
                    return $m[0];
                }
                // Nicht-JS-Typen (JSON-LD, importmap, module, bereits neutralisiert)
                // unangetastet lassen.
                if (preg_match('/\btype\s*=\s*([\'"]?)([^\'">\s]+)\1/i', $attrs, $tm)) {
                    $type = strtolower($tm[2]);
                    if ($type !== 'text/javascript' && $type !== 'application/javascript') {
                        return $m[0];
                    }
                }
                if (trim($body) === '') {
                    return $m[0];
                }

                // Kategorie bestimmen – marketing hat Vorrang (strenger).
                $category = null;
                foreach (array('marketing', 'analytics') as $cat) {
                    foreach ($patterns[$cat] as $re) {
                        if (preg_match($re, $body)) { $category = $cat; break 2; }
                    }
                }
                if (!$category) {
                    return $m[0];
                }

                // type entfernen (falls vorhanden) und neutralisieren.
                $attrs = preg_replace('/\btype\s*=\s*([\'"]).*?\1/i', '', $attrs);
                $attrs = trim($attrs);

                return '<script type="text/plain" data-complyo-consent="' . esc_attr($category) . '"'
                     . ' data-complyo-inline="1"' . ($attrs ? ' ' . $attrs : '') . '>'
                     . $body . '</script>';
            },
            $html
        );
    }
}
