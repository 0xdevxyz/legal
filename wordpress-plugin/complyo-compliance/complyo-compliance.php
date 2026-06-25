<?php
/**
 * Plugin Name: Complyo Compliance
 * Plugin URI: https://complyo.tech
 * Description: DSGVO-konformes Cookie-Banner und Accessibility-Widget. Konfiguration über app.complyo.tech.
 * Version: 2.4.0
 * Author: Complyo
 * Author URI: https://complyo.tech
 * License: GPL v2 or later
 * License URI: https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain: complyo-compliance
 * Domain Path: /languages
 * Requires at least: 5.6
 * Requires PHP: 7.4
 */

if (!defined('ABSPATH')) {
    exit;
}

define('COMPLYO_VERSION',        '2.4.0');
define('COMPLYO_API_BASE',       'https://api.complyo.de');
define('COMPLYO_APP_URL',        'https://app.complyo.tech');
define('COMPLYO_PLUGIN_DIR',     plugin_dir_path(__FILE__));
define('COMPLYO_PLUGIN_URL',     plugin_dir_url(__FILE__));
define('COMPLYO_PLUGIN_BASE',    plugin_basename(__FILE__));
define('COMPLYO_OPTION_SITE_ID', 'complyo_site_id');
define('COMPLYO_OPTION_COOKIE',  'complyo_enable_cookie_banner');
define('COMPLYO_OPTION_A11Y',    'complyo_enable_accessibility');
define('COMPLYO_OPTION_TCF',     'complyo_enable_tcf');
define('COMPLYO_OPTION_SCANNER', 'complyo_enable_scanner');
define('COMPLYO_OPTION_LOCAL_FONTS', 'complyo_enable_local_fonts');
define('COMPLYO_OPTION_INLINE_BLOCKER', 'complyo_enable_inline_blocker');
define('COMPLYO_OPTION_A11Y_STATEMENT', 'complyo_a11y_statement_url');
define('COMPLYO_OPTION_A11Y_FEEDBACK',  'complyo_a11y_feedback');

require_once COMPLYO_PLUGIN_DIR . 'includes/class-complyo-local-fonts.php';
require_once COMPLYO_PLUGIN_DIR . 'includes/class-complyo-inline-blocker.php';

class Complyo_Compliance {

    private static $instance = null;

    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    private function __construct() {
        register_activation_hook(__FILE__,   array($this, 'activate'));
        register_deactivation_hook(__FILE__, array($this, 'deactivate'));

        add_action('plugins_loaded',         array($this, 'load_textdomain'));
        add_action('admin_menu',             array($this, 'add_admin_menu'));
        add_action('admin_init',             array($this, 'register_settings'));
        add_action('admin_enqueue_scripts',  array($this, 'admin_enqueue_scripts'));
        add_filter('plugin_action_links_' . COMPLYO_PLUGIN_BASE, array($this, 'add_settings_link'));

        // Cookie-Blocker muss als allererster Script im <head> erscheinen
        // Damit wird sichergestellt dass kein Tracking-Script vor dem Consent läuft
        add_action('wp_head',   array($this, 'output_cookie_blocker'), 1);

        // Banner + A11y am Ende von <body> (niedrige Priorität = spät)
        add_action('wp_footer', array($this, 'output_banner_script'), 1);

        // Shortcodes: Cookie-Einstellungen anzeigen/widerrufen (Footer/Menü)
        add_shortcode('complyo_cookie_settings', array($this, 'shortcode_cookie_settings'));
        add_shortcode('complyo_cookie_revoke',   array($this, 'shortcode_cookie_revoke'));
        // Menüs rendern standardmäßig keine Shortcodes – nachrüsten:
        add_filter('wp_nav_menu_items', array($this, 'do_shortcode_in_menu'), 10, 2);

        // Caching-Plugin-Kompatibilität
        add_filter('rocket_exclude_js',         array($this, 'exclude_from_rocket'));
        add_filter('rocket_delay_js_exclusions', array($this, 'exclude_from_rocket'));
        add_filter('w3tc_minify_js_do_tag_minification', array($this, 'exclude_from_w3tc'), 10, 3);
        add_filter('autoptimize_filter_js_exclude', array($this, 'exclude_from_autoptimize'));
        add_filter('litespeed_optimize_js_excludes',    array($this, 'exclude_from_litespeed'));
        add_filter('sgo_js_async_execution_exclusions',  array($this, 'exclude_from_siteground'));

        // Google Fonts lokal laden (DSGVO) – eigene Klasse
        Complyo_Local_Fonts::get_instance();

        // Server-seitiges Inline-Script-Blocking – eigene Klasse
        Complyo_Inline_Blocker::get_instance();
    }

    // =========================================================================
    // Activation / Deactivation
    // =========================================================================

    public function activate() {
        if (get_option(COMPLYO_OPTION_SITE_ID) === false || get_option(COMPLYO_OPTION_SITE_ID) === '') {
            update_option(COMPLYO_OPTION_SITE_ID, $this->generate_site_id());
        }
        if (get_option(COMPLYO_OPTION_COOKIE) === false) {
            update_option(COMPLYO_OPTION_COOKIE, '1');
        }
        if (get_option(COMPLYO_OPTION_A11Y) === false) {
            update_option(COMPLYO_OPTION_A11Y, '0');
        }
        if (get_option(COMPLYO_OPTION_TCF) === false) {
            update_option(COMPLYO_OPTION_TCF, '0');
        }
        if (get_option(COMPLYO_OPTION_SCANNER) === false) {
            update_option(COMPLYO_OPTION_SCANNER, '1');
        }
        if (get_option(COMPLYO_OPTION_LOCAL_FONTS) === false) {
            update_option(COMPLYO_OPTION_LOCAL_FONTS, '0');
        }
        if (get_option(COMPLYO_OPTION_INLINE_BLOCKER) === false) {
            update_option(COMPLYO_OPTION_INLINE_BLOCKER, '0');
        }
    }

    public function deactivate() {
        // Optionen bleiben erhalten, damit die Konfiguration bei Re-Aktivierung erhalten bleibt
    }

    public function load_textdomain() {
        load_plugin_textdomain('complyo-compliance', false, dirname(COMPLYO_PLUGIN_BASE) . '/languages');
    }

    // =========================================================================
    // Helpers
    // =========================================================================

    private function generate_site_id() {
        $domain  = parse_url(home_url(), PHP_URL_HOST);
        $domain  = preg_replace('/^www\./', '', $domain);
        return sanitize_key(str_replace('.', '-', strtolower($domain)));
    }

    private function get_site_id() {
        $id = get_option(COMPLYO_OPTION_SITE_ID, '');
        return !empty($id) ? $id : $this->generate_site_id();
    }

    // =========================================================================
    // Script Output
    // =========================================================================

    /**
     * Cookie-Blocker wird als allererster Script in <head> priority 1 ausgegeben.
     * Ohne defer/async, damit er synchron vor allem anderen läuft.
     * Kompatibel mit WP Rocket, W3TC, Autoptimize, LiteSpeed, SiteGround.
     */
    public function output_cookie_blocker() {
        if (get_option(COMPLYO_OPTION_COOKIE, '1') !== '1') {
            return;
        }
        if (is_admin()) {
            return;
        }

        $site_id = esc_attr($this->get_site_id());
        $api     = esc_url(COMPLYO_API_BASE);

        // data-cfasync="false"   → Cloudflare Rocket Loader überspringen
        // data-no-optimize       → Autoptimize überspringen
        // data-no-defer          → SiteGround überspringen
        // Kein async/defer       → Synchron laden (PFLICHT für Blocker)
        echo "\n<!-- Complyo Cookie-Blocker: lädt synchron, muss vor allen anderen Scripts stehen -->\n";
        echo '<script src="' . $api . '/public/cookie-blocker.js"'
            . ' data-site-id="' . $site_id . '"'
            . ' data-cfasync="false"'
            . ' data-no-optimize="1"'
            . ' data-no-defer="1"'
            . '></script>' . "\n";
    }

    /**
     * Cookie-Banner und Accessibility-Widget am Ende von <body>.
     * async ist hier korrekt – Banner kann nach DOM-Aufbau initialisieren.
     */
    public function output_banner_script() {
        if (is_admin()) {
            return;
        }

        $site_id      = esc_attr($this->get_site_id());
        $api          = esc_url(COMPLYO_API_BASE);
        $enable_cookie = get_option(COMPLYO_OPTION_COOKIE, '1');
        $enable_a11y   = get_option(COMPLYO_OPTION_A11Y, '0');
        $enable_tcf    = get_option(COMPLYO_OPTION_TCF, '0');

        if ($enable_cookie !== '1' && $enable_a11y !== '1') {
            return;
        }

        echo "\n<!-- Complyo Compliance Widgets -->\n";

        if ($enable_cookie === '1') {
            $tcf_attr = ($enable_tcf === '1') ? ' data-tcf="true"' : '';
            echo '<script src="' . $api . '/api/widgets/cookie-compliance.js"'
                . ' data-site-id="' . $site_id . '"'
                . $tcf_attr
                . ' data-cfasync="false"'
                . ' data-no-optimize="1"'
                . ' async'
                . '></script>' . "\n";
        }

        if ($enable_a11y === '1') {
            $a11y_statement = get_option(COMPLYO_OPTION_A11Y_STATEMENT, '');
            $a11y_feedback  = get_option(COMPLYO_OPTION_A11Y_FEEDBACK, '');
            $statement_attr = $a11y_statement !== '' ? ' data-a11y-statement-url="' . esc_url($a11y_statement) . '"' : '';
            $feedback_attr  = $a11y_feedback  !== '' ? ' data-a11y-feedback="' . esc_attr($a11y_feedback) . '"' : '';
            echo '<script src="' . $api . '/api/widgets/accessibility.js"'
                . ' data-site-id="' . $site_id . '"'
                . ' data-auto-fix="true"'
                . ' data-show-toolbar="true"'
                . $statement_attr
                . $feedback_attr
                . ' data-cfasync="false"'
                . ' data-no-optimize="1"'
                . ' async'
                . '></script>' . "\n";
        }

        echo "<!-- End Complyo Compliance Widgets -->\n\n";
    }

    // =========================================================================
    // Shortcodes
    // =========================================================================

    /**
     * [complyo_cookie_settings] – Link/Button, der die Cookie-Einstellungen
     * öffnet (aktuelle Auswahl ansehen und ändern).
     *
     * Attribute:
     *   text  – Beschriftung (Standard: "Cookie-Einstellungen")
     *   class – zusätzliche CSS-Klassen
     *   style – "link" (Standard) oder "button"
     *
     * Beispiel: [complyo_cookie_settings text="Cookie-Einstellungen ändern"]
     */
    public function shortcode_cookie_settings($atts) {
        $atts = shortcode_atts(array(
            'text'  => __('Cookie-Einstellungen', 'complyo-compliance'),
            'class' => '',
            'style' => 'link',
        ), $atts, 'complyo_cookie_settings');

        return $this->render_consent_link('settings', $atts);
    }

    /**
     * [complyo_cookie_revoke] – Link/Button, der die erteilte Einwilligung
     * widerruft und den Banner erneut anzeigt.
     *
     * Attribute: text, class, style (wie oben)
     * Beispiel: [complyo_cookie_revoke text="Cookies widerrufen"]
     */
    public function shortcode_cookie_revoke($atts) {
        $atts = shortcode_atts(array(
            'text'  => __('Cookies widerrufen', 'complyo-compliance'),
            'class' => '',
            'style' => 'link',
        ), $atts, 'complyo_cookie_revoke');

        return $this->render_consent_link('revoke', $atts);
    }

    /**
     * Erzeugt das Markup für die Consent-Shortcodes. Das Banner-Script bindet
     * Klicks automatisch über die data-Attribute (CSP-sicher, kein inline-JS).
     */
    private function render_consent_link($action, $atts) {
        $data_attr = ($action === 'revoke') ? 'data-complyo-revoke' : 'data-complyo-settings';

        $classes = 'complyo-consent-link';
        if ($atts['style'] === 'button') {
            $classes .= ' complyo-consent-button';
        }
        if (!empty($atts['class'])) {
            $classes .= ' ' . $atts['class'];
        }

        return sprintf(
            '<a href="#" %s="true" class="%s" style="cursor:pointer;">%s</a>',
            esc_attr($data_attr),
            esc_attr(trim($classes)),
            esc_html($atts['text'])
        );
    }

    /**
     * Erlaubt die Verwendung der Shortcodes direkt in WordPress-Menüs.
     */
    public function do_shortcode_in_menu($items, $args) {
        if (strpos($items, '[complyo_cookie_') !== false) {
            $items = do_shortcode($items);
        }
        return $items;
    }

    // =========================================================================
    // Caching-Plugin-Kompatibilität
    // =========================================================================

    private function get_script_patterns() {
        return array(
            'cookie-blocker.js',
            'cookie-compliance.js',
            'privacy-manager.js',
            'accessibility.js',
            'api.complyo.de',
            'api.complyo.tech',
        );
    }

    public function exclude_from_rocket($exclusions) {
        if (!is_array($exclusions)) {
            $exclusions = array();
        }
        return array_merge($exclusions, $this->get_script_patterns());
    }

    public function exclude_from_w3tc($do_minify, $script_tag, $script_src) {
        foreach ($this->get_script_patterns() as $pattern) {
            if (strpos($script_src, $pattern) !== false) {
                return false;
            }
        }
        return $do_minify;
    }

    public function exclude_from_autoptimize($exclusions) {
        $patterns = implode(',', $this->get_script_patterns());
        return $exclusions . ',' . $patterns;
    }

    public function exclude_from_litespeed($exclusions) {
        if (!is_array($exclusions)) {
            $exclusions = array();
        }
        return array_merge($exclusions, $this->get_script_patterns());
    }

    public function exclude_from_siteground($exclusions) {
        if (!is_array($exclusions)) {
            $exclusions = array();
        }
        return array_merge($exclusions, $this->get_script_patterns());
    }

    // =========================================================================
    // Admin
    // =========================================================================

    public function add_admin_menu() {
        add_options_page(
            __('Complyo Compliance', 'complyo-compliance'),
            __('Complyo Compliance', 'complyo-compliance'),
            'manage_options',
            'complyo-compliance',
            array($this, 'render_admin_page')
        );
    }

    public function register_settings() {
        $args_string = array(
            'type'              => 'string',
            'sanitize_callback' => 'sanitize_text_field',
            'default'           => '',
        );
        $args_flag = array(
            'type'              => 'string',
            'sanitize_callback' => 'sanitize_text_field',
            'default'           => '0',
        );

        register_setting('complyo_settings_group', COMPLYO_OPTION_SITE_ID,  $args_string);
        register_setting('complyo_settings_group', COMPLYO_OPTION_COOKIE,   $args_flag);
        register_setting('complyo_settings_group', COMPLYO_OPTION_A11Y,     $args_flag);
        register_setting('complyo_settings_group', COMPLYO_OPTION_TCF,      $args_flag);
        register_setting('complyo_settings_group', COMPLYO_OPTION_SCANNER,  $args_flag);
        register_setting('complyo_settings_group', COMPLYO_OPTION_LOCAL_FONTS, $args_flag);
        register_setting('complyo_settings_group', COMPLYO_OPTION_INLINE_BLOCKER, $args_flag);
        register_setting('complyo_settings_group', COMPLYO_OPTION_A11Y_STATEMENT, array(
            'type'              => 'string',
            'sanitize_callback' => 'esc_url_raw',
            'default'           => '',
        ));
        register_setting('complyo_settings_group', COMPLYO_OPTION_A11Y_FEEDBACK, $args_string);
    }

    public function admin_enqueue_scripts($hook) {
        if ($hook !== 'settings_page_complyo-compliance') {
            return;
        }
        wp_enqueue_style(
            'complyo-admin',
            COMPLYO_PLUGIN_URL . 'assets/admin.css',
            array(),
            COMPLYO_VERSION
        );
    }

    public function render_admin_page() {
        if (!current_user_can('manage_options')) {
            wp_die(esc_html__('Keine Berechtigung.', 'complyo-compliance'));
        }

        $site_id      = $this->get_site_id();
        $enable_cookie = get_option(COMPLYO_OPTION_COOKIE, '1');
        $enable_a11y   = get_option(COMPLYO_OPTION_A11Y, '0');
        $a11y_statement = get_option(COMPLYO_OPTION_A11Y_STATEMENT, '');
        $a11y_feedback  = get_option(COMPLYO_OPTION_A11Y_FEEDBACK, '');
        $enable_tcf    = get_option(COMPLYO_OPTION_TCF, '0');
        $enable_scanner = get_option(COMPLYO_OPTION_SCANNER, '1');
        $enable_fonts   = get_option(COMPLYO_OPTION_LOCAL_FONTS, '0');
        $enable_inline  = get_option(COMPLYO_OPTION_INLINE_BLOCKER, '0');
        $fonts_count    = Complyo_Local_Fonts::get_instance()->localized_count();
        $app_url      = COMPLYO_APP_URL;
        $api_base     = COMPLYO_API_BASE;
        ?>
        <?php if (isset($_GET['complyo_fonts'])) :
            $cf_found     = isset($_GET['cf_found'])     ? (int) $_GET['cf_found']     : 0;
            $cf_localized = isset($_GET['cf_localized']) ? (int) $_GET['cf_localized'] : 0;
            $cf_errors    = isset($_GET['cf_errors'])    ? (int) $_GET['cf_errors']    : 0; ?>
            <div class="notice notice-<?php echo $cf_errors > 0 ? 'warning' : 'success'; ?> is-dismissible">
                <p><?php
                    printf(
                        esc_html__('Google Fonts lokalisiert: %1$d gefunden, %2$d lokal gespeichert, %3$d Fehler.', 'complyo-compliance'),
                        $cf_found, $cf_localized, $cf_errors
                    );
                    if ($cf_localized > 0) {
                        echo ' ' . esc_html__('Bitte ggf. Caching-Plugin-Cache leeren.', 'complyo-compliance');
                    }
                ?></p>
            </div>
        <?php endif; ?>
        <div class="wrap complyo-wrap">
            <div class="complyo-header">
                <h1>Complyo Compliance</h1>
                <a href="<?php echo esc_url($app_url); ?>" target="_blank" class="complyo-dashboard-btn">
                    <?php esc_html_e('Dashboard öffnen', 'complyo-compliance'); ?> →
                </a>
            </div>

            <?php settings_errors('complyo_settings_group'); ?>

            <form method="post" action="options.php">
                <?php settings_fields('complyo_settings_group'); ?>

                <div class="complyo-card">
                    <h2><?php esc_html_e('Verbindung', 'complyo-compliance'); ?></h2>
                    <table class="form-table" role="presentation">
                        <tr>
                            <th scope="row">
                                <label for="complyo_site_id"><?php esc_html_e('Site-ID', 'complyo-compliance'); ?></label>
                            </th>
                            <td>
                                <input type="text"
                                       id="complyo_site_id"
                                       name="<?php echo esc_attr(COMPLYO_OPTION_SITE_ID); ?>"
                                       value="<?php echo esc_attr($site_id); ?>"
                                       class="regular-text"
                                       required />
                                <p class="description">
                                    <?php esc_html_e('Ihre eindeutige Site-ID aus dem Complyo-Dashboard.', 'complyo-compliance'); ?>
                                    <a href="<?php echo esc_url($app_url . '/settings'); ?>" target="_blank">
                                        <?php esc_html_e('Site-ID anzeigen', 'complyo-compliance'); ?>
                                    </a>
                                </p>
                            </td>
                        </tr>
                    </table>
                </div>

                <div class="complyo-card">
                    <h2><?php esc_html_e('Module', 'complyo-compliance'); ?></h2>
                    <table class="form-table" role="presentation">
                        <tr>
                            <th scope="row"><?php esc_html_e('Cookie-Banner', 'complyo-compliance'); ?></th>
                            <td>
                                <label>
                                    <input type="checkbox"
                                           name="<?php echo esc_attr(COMPLYO_OPTION_COOKIE); ?>"
                                           value="1"
                                           <?php checked($enable_cookie, '1'); ?> />
                                    <?php esc_html_e('DSGVO-konformes Cookie-Consent-Banner aktivieren', 'complyo-compliance'); ?>
                                </label>
                            </td>
                        </tr>
                        <tr>
                            <th scope="row"><?php esc_html_e('IAB TCF 2.2 (Coming Soon)', 'complyo-compliance'); ?></th>
                            <td>
                                <label>
                                    <input type="checkbox"
                                           name="<?php echo esc_attr(COMPLYO_OPTION_TCF); ?>"
                                           value="1"
                                           <?php checked($enable_tcf, '1'); ?> />
                                    <?php esc_html_e('IAB Transparency & Consent Framework 2.2 (in Vorbereitung – noch nicht produktiv nutzen)', 'complyo-compliance'); ?>
                                </label>
                                <p class="description">
                                    <strong><?php esc_html_e('Coming Soon:', 'complyo-compliance'); ?></strong>
                                    <?php esc_html_e('Complyo ist noch nicht als IAB-registriertes CMP zertifiziert. Diese Option aktiviert vorerst nur einen Test-Stub (cmpId 0) und ist KEIN Ersatz für ein registriertes TCF-CMP – für Google Ads / DV360 / Programmatic noch nicht verwenden.', 'complyo-compliance'); ?>
                                </p>
                                <div class="complyo-notice-adsense">
                                    <strong><?php esc_html_e('Sie nutzen Google AdSense?', 'complyo-compliance'); ?></strong><br>
                                    <?php esc_html_e('Google stellt ein kostenloses eigenes CMP-Tool (ID 300) bereit, das direkt in AdSense aktiviert werden kann – ohne zusätzliche Kosten.', 'complyo-compliance'); ?>
                                    <br>
                                    <a href="https://support.google.com/adsense/answer/13554116" target="_blank" rel="noopener">
                                        <?php esc_html_e('Google Datenschutz-Nachrichten einrichten →', 'complyo-compliance'); ?>
                                    </a>
                                    <span class="complyo-notice-path"><?php esc_html_e('AdSense → Datenschutz und Nachrichten → Nachricht erstellen', 'complyo-compliance'); ?></span>
                                </div>
                            </td>
                        </tr>
                        <tr>
                            <th scope="row"><?php esc_html_e('Cookie-Scanner', 'complyo-compliance'); ?></th>
                            <td>
                                <label>
                                    <input type="checkbox"
                                           name="<?php echo esc_attr(COMPLYO_OPTION_SCANNER); ?>"
                                           value="1"
                                           <?php checked($enable_scanner, '1'); ?> />
                                    <?php esc_html_e('Automatisches Cookie-Scanning aktivieren', 'complyo-compliance'); ?>
                                </label>
                                <p class="description">
                                    <?php esc_html_e('Complyo scannt Ihre Website automatisch auf neue Cookies und aktualisiert die Cookie-Deklaration.', 'complyo-compliance'); ?>
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <th scope="row"><?php esc_html_e('Accessibility-Widget', 'complyo-compliance'); ?></th>
                            <td>
                                <label>
                                    <input type="checkbox"
                                           name="<?php echo esc_attr(COMPLYO_OPTION_A11Y); ?>"
                                           value="1"
                                           <?php checked($enable_a11y, '1'); ?> />
                                    <?php esc_html_e('WCAG 2.2 Level AA Barrierefreiheits-Widget aktivieren', 'complyo-compliance'); ?>
                                </label>
                                <p style="margin-top:12px;">
                                    <label for="complyo_a11y_statement_url"><strong><?php esc_html_e('Barrierefreiheitserklärung (URL)', 'complyo-compliance'); ?></strong></label><br>
                                    <input type="url"
                                           id="complyo_a11y_statement_url"
                                           name="<?php echo esc_attr(COMPLYO_OPTION_A11Y_STATEMENT); ?>"
                                           value="<?php echo esc_attr($a11y_statement); ?>"
                                           class="regular-text"
                                           placeholder="https://ihre-domain.de/barrierefreiheit" />
                                </p>
                                <p style="margin-top:8px;">
                                    <label for="complyo_a11y_feedback"><strong><?php esc_html_e('Barriere melden – Kontakt (E-Mail oder URL)', 'complyo-compliance'); ?></strong></label><br>
                                    <input type="text"
                                           id="complyo_a11y_feedback"
                                           name="<?php echo esc_attr(COMPLYO_OPTION_A11Y_FEEDBACK); ?>"
                                           value="<?php echo esc_attr($a11y_feedback); ?>"
                                           class="regular-text"
                                           placeholder="barrierefreiheit@ihre-domain.de" />
                                </p>
                                <p class="description">
                                    <?php esc_html_e('Diese Links erscheinen im Widget unter „Rechtliches & Barrierefreiheit“. Der Haftungs-Hinweis und die Schlichtungsstelle BGG werden automatisch angezeigt.', 'complyo-compliance'); ?>
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <th scope="row"><?php esc_html_e('Google Fonts lokal', 'complyo-compliance'); ?></th>
                            <td>
                                <label>
                                    <input type="checkbox"
                                           name="<?php echo esc_attr(COMPLYO_OPTION_LOCAL_FONTS); ?>"
                                           value="1"
                                           <?php checked($enable_fonts, '1'); ?> />
                                    <?php esc_html_e('Google Fonts lokal ausliefern (kein Request an Google – DSGVO, LG München)', 'complyo-compliance'); ?>
                                </label>
                                <p class="description">
                                    <?php esc_html_e('Externe Google-Fonts-Stylesheets werden auf den eigenen Server kopiert und in der Seite ersetzt. Damit verlässt vor dem Consent keine IP-Adresse die Website an Google.', 'complyo-compliance'); ?>
                                    <?php if ($fonts_count > 0) : ?>
                                        <br><strong><?php printf(esc_html__('%d lokalisierte Font-Stylesheets.', 'complyo-compliance'), (int) $fonts_count); ?></strong>
                                    <?php endif; ?>
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <th scope="row"><?php esc_html_e('Inline-Tracker blockieren', 'complyo-compliance'); ?></th>
                            <td>
                                <label>
                                    <input type="checkbox"
                                           name="<?php echo esc_attr(COMPLYO_OPTION_INLINE_BLOCKER); ?>"
                                           value="1"
                                           <?php checked($enable_inline, '1'); ?> />
                                    <?php esc_html_e('Inline-Tracking-Snippets server-seitig vor Consent neutralisieren', 'complyo-compliance'); ?>
                                </label>
                                <p class="description">
                                    <?php esc_html_e('Neutralisiert direkt im HTML eingebettete Tracker (Google Analytics/gtag, Meta Pixel, Hotjar, Matomo, LinkedIn, TikTok, Pinterest, Bing, Clarity), die client-seitig nicht zuverlässig stoppbar sind. Nach Einwilligung werden sie automatisch nachgeladen.', 'complyo-compliance'); ?>
                                    <br><em><?php esc_html_e('Empfohlen, aber nach dem Aktivieren bitte Seite + zentrale Funktionen testen (konservativ kuratierte Muster).', 'complyo-compliance'); ?></em>
                                </p>
                            </td>
                        </tr>
                    </table>
                </div>

                <?php submit_button(__('Einstellungen speichern', 'complyo-compliance')); ?>
            </form>

            <?php if ($enable_fonts === '1') : ?>
            <div class="complyo-card">
                <h2><?php esc_html_e('Google Fonts lokalisieren', 'complyo-compliance'); ?></h2>
                <p class="description">
                    <?php esc_html_e('Lädt die aktuell auf der Startseite eingebundenen Google Fonts herunter und speichert sie lokal. Neue Fonts auf anderen Seiten werden automatisch im Hintergrund nachgezogen.', 'complyo-compliance'); ?>
                </p>
                <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>">
                    <input type="hidden" name="action" value="complyo_localize_fonts" />
                    <?php wp_nonce_field('complyo_localize_fonts'); ?>
                    <?php submit_button(__('Google Fonts jetzt lokalisieren', 'complyo-compliance'), 'secondary', 'submit', false); ?>
                </form>
            </div>
            <?php endif; ?>

            <div class="complyo-card complyo-card-info">
                <h2><?php esc_html_e('Eingebundene Scripts', 'complyo-compliance'); ?></h2>
                <p><?php esc_html_e('Folgende Scripts werden automatisch eingebunden (Reihenfolge ist entscheidend):', 'complyo-compliance'); ?></p>
                <ol class="complyo-script-list">
                    <li>
                        <strong><?php esc_html_e('Cookie-Blocker', 'complyo-compliance'); ?></strong>
                        — <?php esc_html_e('synchron in &lt;head&gt; priority 1 (blockiert Tracking vor Consent)', 'complyo-compliance'); ?><br>
                        <code><?php echo esc_html($api_base . '/public/cookie-blocker.js'); ?></code>
                    </li>
                    <li>
                        <strong><?php esc_html_e('Cookie-Banner', 'complyo-compliance'); ?></strong>
                        — <?php esc_html_e('async am Ende von &lt;body&gt;', 'complyo-compliance'); ?><br>
                        <code><?php echo esc_html($api_base . '/api/widgets/cookie-compliance.js'); ?></code>
                    </li>
                    <?php if ($enable_a11y === '1') : ?>
                    <li>
                        <strong><?php esc_html_e('Accessibility-Widget', 'complyo-compliance'); ?></strong>
                        — <?php esc_html_e('async am Ende von &lt;body&gt;', 'complyo-compliance'); ?><br>
                        <code><?php echo esc_html($api_base . '/api/widgets/accessibility.js'); ?></code>
                    </li>
                    <?php endif; ?>
                </ol>
                <p class="description">
                    <?php esc_html_e('WP Rocket, W3 Total Cache, Autoptimize, LiteSpeed Cache und SiteGround Optimizer werden automatisch konfiguriert (Scripts werden von Minifizierung und Defer ausgenommen).', 'complyo-compliance'); ?>
                </p>
            </div>

            <div class="complyo-card complyo-card-link">
                <p>
                    <?php esc_html_e('Banner-Design, Texte, Kategorien und Cookie-Deklaration konfigurieren Sie in Ihrem', 'complyo-compliance'); ?>
                    <a href="<?php echo esc_url($app_url); ?>" target="_blank">
                        <?php esc_html_e('Complyo-Dashboard', 'complyo-compliance'); ?>
                    </a>.
                </p>
            </div>
        </div>
        <?php
    }

    public function add_settings_link($links) {
        $link = '<a href="' . esc_url(admin_url('options-general.php?page=complyo-compliance')) . '">'
              . esc_html__('Einstellungen', 'complyo-compliance') . '</a>';
        array_unshift($links, $link);
        return $links;
    }
}

add_action('plugins_loaded', array('Complyo_Compliance', 'get_instance'));
