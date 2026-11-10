<?php
/**
 * Complyo – Tracker im Markup neutralisieren (Joomla).
 *
 * Gleiche Regel wie im WordPress-Plugin seit 2.7.0
 * (wordpress-plugin/complyo-compliance/includes/class-complyo-inline-blocker.php):
 * Der Vorlade-Scanner des Browsers holt statische <script src>, <iframe src> und
 * <link href>, bevor irgendein Skript sie anfassen kann. Der Blocker im Browser
 * kommt dafuer zu spaet; nur Markup ohne src/href verhindert den Abruf.
 *
 *   <script src="https://www.googletagmanager.com/gtag/js?id=G-X">
 *     ->  <script type="text/plain" data-complyo-consent="analytics"
 *                 data-complyo-src="https://www.googletagmanager.com/gtag/js?id=G-X"
 *                 data-complyo-blocked="true">
 *
 * public/cookie-blocker.js gibt die Elemente nach der Einwilligung frei, auch
 * bei wiederkehrenden Besuchern.
 *
 * Die Klasse haengt bewusst nicht an Joomla: sie nimmt HTML und gibt HTML
 * zurueck, damit sie ohne Joomla pruefbar ist (backend/tests/php/).
 * Jeder Fehler heisst: Original zurueckgeben. Eine Seite ohne Neutralisierung
 * ist besser als eine weisse Seite.
 *
 * @package     Complyo
 * @subpackage  plg_system_complyo
 * @license     GPL-2.0-or-later
 */

defined('_JEXEC') or die;

class ComplyoMarkup
{
    private static function scriptPatterns(): array
    {
        return array(
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
    }

    private static function iframePatterns(): array
    {
        return array(
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
    }

    private static function inlinePatterns(): array
    {
        return array(
            'marketing' => array(
                '/\bfbq\s*\(|connect\.facebook\.net|_fbq\b/i',
                '/_linkedin_partner_id|snap\.licdn\.com/i',
                '/\bttq\b|TiktokAnalyticsObject|analytics\.tiktok\.com/i',
                '/\bpintrk\s*\(/i',
                '/\buetq\b|bat\.bing\.com/i',
                '/\bsnaptr\s*\(/i',
            ),
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
        );
    }

    private static function categoryFor(string $text, array $patterns, array $order): ?string
    {
        foreach ($order as $cat) {
            if (empty($patterns[$cat])) {
                continue;
            }
            foreach ($patterns[$cat] as $re) {
                if (preg_match($re, $text)) {
                    return $cat;
                }
            }
        }
        return null;
    }

    private static function esc(string $v): string
    {
        return htmlspecialchars($v, ENT_QUOTES, 'UTF-8');
    }

    /**
     * Neutralisiert externe Tracker, eingebettete Fremdinhalte, Google-Fonts-Links
     * und Inline-Tracker. Gibt bei jedem Fehler das Original zurueck.
     */
    public static function rewrite($html)
    {
        if (!is_string($html) || $html === '' || stripos($html, '<') === false) {
            return $html;
        }
        try {
            $out = self::rewriteExternal($html);
            $out = self::rewriteInline($out);
            return (is_string($out) && $out !== '') ? $out : $html;
        } catch (\Throwable $e) {
            return $html;
        }
    }

    private static function rewriteExternal(string $html): string
    {
        $scriptPat = self::scriptPatterns();
        $iframePat = self::iframePatterns();
        $order     = array('analytics', 'marketing', 'functional');

        // <script src="…"></script>
        $neu = preg_replace_callback(
            '#<script\b([^>]*?)(?<![\w-])src\s*=\s*(["\'])([^"\']+)\2([^>]*)>(\s*)</script>#is',
            function ($m) use ($scriptPat, $order) {
                $url = html_entity_decode($m[3]);
                $cat = self::categoryFor($url, $scriptPat, $order);
                if (!$cat) {
                    return $m[0];
                }
                $attrs = trim($m[1] . ' ' . $m[4]);
                $attrs = trim(preg_replace('/\btype\s*=\s*(["\']).*?\1/i', '', $attrs));
                return '<script type="text/plain" data-complyo-consent="' . self::esc($cat) . '"'
                     . ' data-complyo-src="' . self::esc($url) . '" data-complyo-blocked="true"'
                     . ($attrs !== '' ? ' ' . $attrs : '') . '></script>';
            },
            $html
        );
        if (is_string($neu)) {
            $html = $neu;
        }

        // <iframe src="…">
        $neu = preg_replace_callback(
            '#<iframe\b([^>]*?)(?<![\w-])src\s*=\s*(["\'])([^"\']+)\2([^>]*)>#is',
            function ($m) use ($iframePat, $order) {
                $url = html_entity_decode($m[3]);
                $cat = self::categoryFor($url, $iframePat, $order);
                if (!$cat) {
                    return $m[0];
                }
                $attrs = trim($m[1] . ' ' . $m[4]);
                return '<iframe data-complyo-consent="' . self::esc($cat) . '"'
                     . ' data-complyo-src="' . self::esc($url) . '" data-complyo-blocked="true"'
                     . ($attrs !== '' ? ' ' . $attrs : '') . '>';
            },
            $html
        );
        if (is_string($neu)) {
            $html = $neu;
        }

        // <link href="//fonts.googleapis.com/…"> und Preconnect/Preload auf die Font-Hosts
        $neu = preg_replace_callback(
            '#<link\b([^>]*?)(?<![\w-])href\s*=\s*(["\'])((?:https?:)?//(?:fonts\.googleapis\.com|fonts\.gstatic\.com)[^"\']*)\2([^>]*)>#is',
            function ($m) {
                $url   = html_entity_decode($m[3]);
                $attrs = trim($m[1] . ' ' . $m[4]);
                $rel   = '';
                if (preg_match('/\brel\s*=\s*(["\'])(.*?)\1/i', $attrs, $rm)) {
                    $rel = $rm[2];
                }
                $attrs = trim(preg_replace('/\bmedia\s*=\s*(["\']).*?\1/i', '', $attrs));
                return '<link data-complyo-consent="functional" data-complyo-href="' . self::esc($url) . '"'
                     . ' data-complyo-rel="' . self::esc($rel) . '" data-complyo-blocked="true" media="not all"'
                     . ($attrs !== '' ? ' ' . $attrs : '') . '>';
            },
            $html
        );
        if (is_string($neu)) {
            $html = $neu;
        }

        return $html;
    }

    private static function rewriteInline(string $html): string
    {
        if (stripos($html, '<script') === false) {
            return $html;
        }
        $patterns = self::inlinePatterns();

        $neu = preg_replace_callback(
            '#<script\b([^>]*)>(.*?)</script>#is',
            function ($m) use ($patterns) {
                $attrs = $m[1];
                $body  = $m[2];

                // Externe Skripte sind oben behandelt; bereits neutralisierte bleiben.
                if (preg_match('/(?<![\w-])src\s*=/i', $attrs) || stripos($attrs, 'data-complyo-') !== false) {
                    return $m[0];
                }
                // JSON-LD, importmap, module und alles Nicht-JS unangetastet lassen.
                if (preg_match('/\btype\s*=\s*([\'"]?)([^\'">\s]+)\1/i', $attrs, $tm)) {
                    $type = strtolower($tm[2]);
                    if ($type !== 'text/javascript' && $type !== 'application/javascript') {
                        return $m[0];
                    }
                }
                if (trim($body) === '') {
                    return $m[0];
                }
                $category = self::categoryFor($body, $patterns, array('marketing', 'analytics'));
                if (!$category) {
                    return $m[0];
                }
                $attrs = trim(preg_replace('/\btype\s*=\s*([\'"]).*?\1/i', '', $attrs));
                return '<script type="text/plain" data-complyo-consent="' . self::esc($category) . '"'
                     . ' data-complyo-inline="1"' . ($attrs !== '' ? ' ' . $attrs : '') . '>'
                     . $body . '</script>';
            },
            $html
        );

        return is_string($neu) ? $neu : $html;
    }
}
