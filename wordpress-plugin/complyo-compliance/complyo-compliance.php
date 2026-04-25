<?php
/**
 * Plugin Name: Complyo Compliance
 * Plugin URI: https://complyo.tech
 * Description: DSGVO-konformes Cookie-Banner und Accessibility-Widget. Konfiguration über app.complyo.tech.
 * Version: 2.0.0
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

define('COMPLYO_VERSION',        '2.0.0');
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

        // Caching-Plugin-Kompatibilität
        add_filter('rocket_exclude_js',         array($this, 'exclude_from_rocket'));
        add_filter('rocket_delay_js_exclusions', array($this, 'exclude_from_rocket'));
        add_filter('w3tc_minify_js_do_tag_minification', array($this, 'exclude_from_w3tc'), 10, 3);
        add_filter('autoptimize_filter_js_exclude', array($this, 'exclude_from_autoptimize'));
        add_filter('litespeed_optimize_js_excludes',    array($this, 'exclude_from_litespeed'));
        add_filter('sgo_js_async_execution_exclusions',  array($this, 'exclude_from_siteground'));
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
            echo '<script src="' . $api . '/api/widgets/accessibility.js"'
                . ' data-site-id="' . $site_id . '"'
                . ' data-auto-fix="true"'
                . ' data-show-toolbar="true"'
                . ' data-cfasync="false"'
                . ' data-no-optimize="1"'
                . ' async'
                . '></script>' . "\n";
        }

        echo "<!-- End Complyo Compliance Widgets -->\n\n";
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
        $enable_tcf    = get_option(COMPLYO_OPTION_TCF, '0');
        $enable_scanner = get_option(COMPLYO_OPTION_SCANNER, '1');
        $app_url      = COMPLYO_APP_URL;
        $api_base     = COMPLYO_API_BASE;
        ?>
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
                            <th scope="row"><?php esc_html_e('IAB TCF 2.2', 'complyo-compliance'); ?></th>
                            <td>
                                <label>
                                    <input type="checkbox"
                                           name="<?php echo esc_attr(COMPLYO_OPTION_TCF); ?>"
                                           value="1"
                                           <?php checked($enable_tcf, '1'); ?> />
                                    <?php esc_html_e('IAB Transparency & Consent Framework 2.2 aktivieren (für Google Ads / Programmatic Advertising)', 'complyo-compliance'); ?>
                                </label>
                                <p class="description">
                                    <?php esc_html_e('Pflicht wenn Google Ads, DV360 oder andere IAB-Vendoren eingesetzt werden.', 'complyo-compliance'); ?>
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
                            </td>
                        </tr>
                    </table>
                </div>

                <?php submit_button(__('Einstellungen speichern', 'complyo-compliance')); ?>
            </form>

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
