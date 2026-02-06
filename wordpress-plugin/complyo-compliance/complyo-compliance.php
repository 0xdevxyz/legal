<?php
/**
 * Plugin Name: Complyo Compliance
 * Plugin URI: https://complyo.tech
 * Description: Integriert Complyo Cookie-Banner und Accessibility-Widget sicher in WordPress. DSGVO-konform und WCAG 2.1 Level AA.
 * Version: 1.0.0
 * Author: Complyo
 * Author URI: https://complyo.tech
 * License: GPL v2 or later
 * License URI: https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain: complyo-compliance
 * Domain Path: /languages
 * Requires at least: 5.0
 * Requires PHP: 7.4
 */

// Exit if accessed directly
if (!defined('ABSPATH')) {
    exit;
}

// Define plugin constants
define('COMPLYO_COMPLIANCE_VERSION', '1.0.0');
define('COMPLYO_COMPLIANCE_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('COMPLYO_COMPLIANCE_PLUGIN_URL', plugin_dir_url(__FILE__));
define('COMPLYO_COMPLIANCE_PLUGIN_BASENAME', plugin_basename(__FILE__));

/**
 * Main Plugin Class
 */
class Complyo_Compliance {
    
    private static $instance = null;
    private $site_id = '';
    
    /**
     * Singleton instance
     */
    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }
    
    /**
     * Constructor
     */
    private function __construct() {
        $this->init();
    }
    
    /**
     * Initialize plugin
     */
    private function init() {
        // Load site ID from options
        $this->site_id = get_option('complyo_site_id', '');
        
        // Admin hooks
        add_action('admin_menu', array($this, 'add_admin_menu'));
        add_action('admin_init', array($this, 'register_settings'));
        add_action('admin_enqueue_scripts', array($this, 'admin_enqueue_scripts'));
        
        // Frontend hooks
        add_action('wp_footer', array($this, 'enqueue_widgets'), 999);
        
        // Activation/Deactivation hooks
        register_activation_hook(__FILE__, array($this, 'activate'));
        register_deactivation_hook(__FILE__, array($this, 'deactivate'));
        
        // Add settings link to plugin page
        add_filter('plugin_action_links_' . COMPLYO_COMPLIANCE_PLUGIN_BASENAME, array($this, 'add_settings_link'));
    }
    
    /**
     * Plugin activation
     */
    public function activate() {
        // Set default options if not exists
        if (get_option('complyo_site_id') === false) {
            // Auto-generate site_id from domain
            $domain = parse_url(home_url(), PHP_URL_HOST);
            $domain = str_replace('www.', '', $domain);
            $site_id = str_replace('.', '-', strtolower($domain));
            update_option('complyo_site_id', $site_id);
        }
        
        // Set default settings
        if (get_option('complyo_enable_cookie_banner') === false) {
            update_option('complyo_enable_cookie_banner', '1');
        }
        if (get_option('complyo_enable_accessibility') === false) {
            update_option('complyo_enable_accessibility', '1');
        }
    }
    
    /**
     * Plugin deactivation
     */
    public function deactivate() {
        // Cleanup if needed
    }
    
    /**
     * Add admin menu
     */
    public function add_admin_menu() {
        add_options_page(
            __('Complyo Compliance', 'complyo-compliance'),
            __('Complyo Compliance', 'complyo-compliance'),
            'manage_options',
            'complyo-compliance',
            array($this, 'render_admin_page')
        );
    }
    
    /**
     * Register settings
     */
    public function register_settings() {
        register_setting('complyo_compliance_settings', 'complyo_site_id', array(
            'type' => 'string',
            'sanitize_callback' => 'sanitize_text_field',
            'default' => ''
        ));
        
        register_setting('complyo_compliance_settings', 'complyo_enable_cookie_banner', array(
            'type' => 'string',
            'sanitize_callback' => 'sanitize_text_field',
            'default' => '1'
        ));
        
        register_setting('complyo_compliance_settings', 'complyo_enable_accessibility', array(
            'type' => 'string',
            'sanitize_callback' => 'sanitize_text_field',
            'default' => '1'
        ));
        
        // Add settings sections
        add_settings_section(
            'complyo_main_settings',
            __('Haupteinstellungen', 'complyo-compliance'),
            array($this, 'render_settings_section'),
            'complyo-compliance'
        );
        
        // Add settings fields
        add_settings_field(
            'complyo_site_id',
            __('Site-ID', 'complyo-compliance'),
            array($this, 'render_site_id_field'),
            'complyo-compliance',
            'complyo_main_settings'
        );
        
        add_settings_field(
            'complyo_enable_cookie_banner',
            __('Cookie-Banner aktivieren', 'complyo-compliance'),
            array($this, 'render_cookie_banner_field'),
            'complyo-compliance',
            'complyo_main_settings'
        );
        
        add_settings_field(
            'complyo_enable_accessibility',
            __('Accessibility-Widget aktivieren', 'complyo-compliance'),
            array($this, 'render_accessibility_field'),
            'complyo-compliance',
            'complyo_main_settings'
        );
    }
    
    /**
     * Render settings section
     */
    public function render_settings_section() {
        echo '<p>' . esc_html__('Konfigurieren Sie Ihre Complyo Compliance-Integration.', 'complyo-compliance') . '</p>';
    }
    
    /**
     * Render Site-ID field
     */
    public function render_site_id_field() {
        $site_id = get_option('complyo_site_id', '');
        $domain = parse_url(home_url(), PHP_URL_HOST);
        $domain = str_replace('www.', '', $domain);
        $auto_site_id = str_replace('.', '-', strtolower($domain));
        
        ?>
        <input type="text" 
               name="complyo_site_id" 
               value="<?php echo esc_attr($site_id); ?>" 
               class="regular-text" 
               placeholder="<?php echo esc_attr($auto_site_id); ?>"
               required />
        <p class="description">
            <?php esc_html_e('Ihre eindeutige Site-ID. Wird automatisch aus Ihrer Domain generiert, falls leer.', 'complyo-compliance'); ?>
            <br>
            <strong><?php esc_html_e('Beispiel:', 'complyo-compliance'); ?></strong> 
            <?php echo esc_html($domain); ?> → <code><?php echo esc_html($auto_site_id); ?></code>
        </p>
        <?php
    }
    
    /**
     * Render Cookie Banner field
     */
    public function render_cookie_banner_field() {
        $enabled = get_option('complyo_enable_cookie_banner', '1');
        ?>
        <label>
            <input type="checkbox" 
                   name="complyo_enable_cookie_banner" 
                   value="1" 
                   <?php checked($enabled, '1'); ?> />
            <?php esc_html_e('Cookie-Banner aktivieren (DSGVO-konform)', 'complyo-compliance'); ?>
        </label>
        <p class="description">
            <?php esc_html_e('Zeigt ein DSGVO-konformes Cookie-Consent-Banner an.', 'complyo-compliance'); ?>
        </p>
        <?php
    }
    
    /**
     * Render Accessibility field
     */
    public function render_accessibility_field() {
        $enabled = get_option('complyo_enable_accessibility', '1');
        ?>
        <label>
            <input type="checkbox" 
                   name="complyo_enable_accessibility" 
                   value="1" 
                   <?php checked($enabled, '1'); ?> />
            <?php esc_html_e('Accessibility-Widget aktivieren (WCAG 2.1 Level AA)', 'complyo-compliance'); ?>
        </label>
        <p class="description">
            <?php esc_html_e('Zeigt ein Barrierefreiheits-Widget für WCAG 2.1 Level AA Konformität an.', 'complyo-compliance'); ?>
        </p>
        <?php
    }
    
    /**
     * Render admin page
     */
    public function render_admin_page() {
        if (!current_user_can('manage_options')) {
            wp_die(__('Sie haben keine Berechtigung, auf diese Seite zuzugreifen.', 'complyo-compliance'));
        }
        
        // Handle form submission
        if (isset($_POST['submit']) && check_admin_referer('complyo_compliance_settings')) {
            // Auto-generate site_id if empty
            if (empty($_POST['complyo_site_id'])) {
                $domain = parse_url(home_url(), PHP_URL_HOST);
                $domain = str_replace('www.', '', $domain);
                $_POST['complyo_site_id'] = str_replace('.', '-', strtolower($domain));
            }
        }
        
        ?>
        <div class="wrap">
            <h1><?php esc_html_e('Complyo Compliance', 'complyo-compliance'); ?></h1>
            
            <div class="card" style="max-width: 800px;">
                <h2><?php esc_html_e('Integration', 'complyo-compliance'); ?></h2>
                <p>
                    <?php esc_html_e('Dieses Plugin bindet automatisch die Complyo Widgets in Ihre WordPress-Website ein:', 'complyo-compliance'); ?>
                </p>
                <ul>
                    <li><strong><?php esc_html_e('Cookie-Banner:', 'complyo-compliance'); ?></strong> <?php esc_html_e('DSGVO-konformes Cookie-Consent-Management', 'complyo-compliance'); ?></li>
                    <li><strong><?php esc_html_e('Accessibility-Widget:', 'complyo-compliance'); ?></strong> <?php esc_html_e('WCAG 2.1 Level AA Barrierefreiheits-Tools', 'complyo-compliance'); ?></li>
                </ul>
            </div>
            
            <form method="post" action="options.php">
                <?php
                settings_fields('complyo_compliance_settings');
                do_settings_sections('complyo-compliance');
                submit_button();
                ?>
            </form>
            
            <div class="card" style="max-width: 800px; margin-top: 20px;">
                <h2><?php esc_html_e('Integration-Code', 'complyo-compliance'); ?></h2>
                <p><?php esc_html_e('Der folgende Code wird automatisch in den Footer Ihrer Website eingefügt:', 'complyo-compliance'); ?></p>
                <textarea readonly class="large-text code" rows="8" style="font-family: monospace; font-size: 12px;"><?php
                    $site_id = get_option('complyo_site_id', '');
                    if (empty($site_id)) {
                        $domain = parse_url(home_url(), PHP_URL_HOST);
                        $domain = str_replace('www.', '', $domain);
                        $site_id = str_replace('.', '-', strtolower($domain));
                    }
                    
                    echo esc_html("<!-- Complyo Cookie Blocker (muss ZUERST geladen werden) -->\n");
                    echo esc_html('<script src="https://api.complyo.tech/public/cookie-blocker.js" data-site-id="' . $site_id . '"></script>' . "\n\n");
                    echo esc_html("<!-- Complyo Cookie Banner -->\n");
                    echo esc_html('<script src="https://api.complyo.tech/api/widgets/cookie-compliance.js" data-site-id="' . $site_id . '" async></script>' . "\n\n");
                    echo esc_html("<!-- Complyo Accessibility Widget -->\n");
                    echo esc_html('<script src="https://api.complyo.tech/api/widgets/accessibility.js" data-site-id="' . $site_id . '" data-auto-fix="true" data-show-toolbar="true" async></script>');
                ?></textarea>
            </div>
            
            <div class="card" style="max-width: 800px; margin-top: 20px; background: #fff3cd; border-left: 4px solid #ffc107;">
                <h2 style="margin-top: 0;"><?php esc_html_e('Wichtiger Hinweis', 'complyo-compliance'); ?></h2>
                <p>
                    <strong><?php esc_html_e('Konfiguration:', 'complyo-compliance'); ?></strong>
                    <?php esc_html_e('Die Cookie-Banner-Konfiguration (Farben, Texte, Services) erfolgt über Ihr Complyo-Dashboard unter', 'complyo-compliance'); ?>
                    <a href="https://app.complyo.tech" target="_blank">app.complyo.tech</a>.
                </p>
                <p>
                    <strong><?php esc_html_e('Support:', 'complyo-compliance'); ?></strong>
                    <?php esc_html_e('Bei Fragen oder Problemen kontaktieren Sie', 'complyo-compliance'); ?>
                    <a href="mailto:support@complyo.tech">support@complyo.tech</a>.
                </p>
            </div>
        </div>
        <?php
    }
    
    /**
     * Enqueue admin scripts
     */
    public function admin_enqueue_scripts($hook) {
        if ($hook !== 'settings_page_complyo-compliance') {
            return;
        }
        
        wp_enqueue_style(
            'complyo-compliance-admin',
            COMPLYO_COMPLIANCE_PLUGIN_URL . 'assets/admin.css',
            array(),
            COMPLYO_COMPLIANCE_VERSION
        );
    }
    
    /**
     * Enqueue widgets in footer
     */
    public function enqueue_widgets() {
        // Get settings
        $site_id = get_option('complyo_site_id', '');
        $enable_cookie = get_option('complyo_enable_cookie_banner', '1');
        $enable_accessibility = get_option('complyo_enable_accessibility', '1');
        
        // Auto-generate site_id if empty
        if (empty($site_id)) {
            $domain = parse_url(home_url(), PHP_URL_HOST);
            $domain = str_replace('www.', '', $domain);
            $site_id = str_replace('.', '-', strtolower($domain));
        }
        
        // Don't output if both disabled
        if ($enable_cookie !== '1' && $enable_accessibility !== '1') {
            return;
        }
        
        // Output scripts
        echo "\n<!-- Complyo Compliance Widgets -->\n";
        
        // Cookie Blocker (muss ZUERST geladen werden, wenn Cookie-Banner aktiviert)
        if ($enable_cookie === '1') {
            echo '<script src="https://api.complyo.tech/public/cookie-blocker.js" data-site-id="' . esc_attr($site_id) . '"></script>' . "\n";
        }
        
        // Cookie Banner
        if ($enable_cookie === '1') {
            echo '<script src="https://api.complyo.tech/api/widgets/cookie-compliance.js" data-site-id="' . esc_attr($site_id) . '" data-complyo-site-id="' . esc_attr($site_id) . '" async></script>' . "\n";
        }
        
        // Accessibility Widget
        if ($enable_accessibility === '1') {
            echo '<script src="https://api.complyo.tech/api/widgets/accessibility.js" data-site-id="' . esc_attr($site_id) . '" data-auto-fix="true" data-show-toolbar="true" async></script>' . "\n";
        }
        
        echo "<!-- End Complyo Compliance Widgets -->\n";
    }
    
    /**
     * Add settings link to plugin page
     */
    public function add_settings_link($links) {
        $settings_link = '<a href="' . admin_url('options-general.php?page=complyo-compliance') . '">' . __('Einstellungen', 'complyo-compliance') . '</a>';
        array_unshift($links, $settings_link);
        return $links;
    }
}

// Initialize plugin
function complyo_compliance_init() {
    return Complyo_Compliance::get_instance();
}

// Start plugin
add_action('plugins_loaded', 'complyo_compliance_init');
