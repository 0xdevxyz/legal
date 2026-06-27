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
 * (unblockInlineScript). Externe <script src> werden separat client-seitig
 * geblockt; hier geht es ausschließlich um Inline-Code.
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
            add_action('template_redirect', array($this, 'start_buffer'), 1);
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

    public function start_buffer() {
        if (is_admin() || is_feed() || (defined('REST_REQUEST') && REST_REQUEST) || wp_doing_ajax()) {
            return;
        }
        ob_start(array($this, 'rewrite'));
    }

    /**
     * Findet Inline-<script>-Blöcke und neutralisiert Tracker.
     */
    public function rewrite($html) {
        if (!is_string($html) || stripos($html, '<script') === false) {
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
