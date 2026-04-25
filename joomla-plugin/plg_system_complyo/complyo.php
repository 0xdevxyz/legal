<?php
/**
 * Complyo Compliance – Joomla System Plugin
 *
 * Bindet den Complyo Cookie-Blocker (synchron im <head>),
 * das Cookie-Banner und optional das Accessibility-Widget
 * DSGVO-konform in Joomla ein.
 *
 * @package     Complyo
 * @subpackage  plg_system_complyo
 * @license     GPL-2.0-or-later
 */

defined('_JEXEC') or die;

use Joomla\CMS\Plugin\CMSPlugin;
use Joomla\CMS\Factory;

class PlgSystemComplyo extends CMSPlugin
{
    const API_BASE = 'https://api.complyo.de';
    const APP_URL  = 'https://app.complyo.tech';

    protected $autoloadLanguage = true;

    /**
     * onAfterInitialise – frühestmöglicher Hook.
     * Hier registrieren wir den Head-Output-Buffer-Callback,
     * damit der Cookie-Blocker wirklich als erstes Script erscheint.
     */
    public function onAfterInitialise(): void
    {
        $app = Factory::getApplication();

        if (!$app->isClient('site')) {
            return;
        }

        if ($this->params->get('enable_cookie_banner', 1)) {
            // Cookie-Blocker synchron in <head> einfügen
            // Wir hängen uns an den Document-Head-Event
            $app->getDocument()->addCustomTag($this->buildBlockerTag());
        }
    }

    /**
     * onBeforeCompileHead – wird kurz vor </head> aufgerufen.
     * Doppelte Sicherheit: Falls onAfterInitialise nicht greift.
     */
    public function onBeforeCompileHead(): void
    {
        $app = Factory::getApplication();

        if (!$app->isClient('site')) {
            return;
        }

        // Nichts weiter hier – Blocker bereits via onAfterInitialise hinzugefügt
    }

    /**
     * onAfterRender – fügt Banner-Script vor </body> ein.
     */
    public function onAfterRender(): void
    {
        $app = Factory::getApplication();

        if (!$app->isClient('site')) {
            return;
        }

        $enable_cookie = (bool) $this->params->get('enable_cookie_banner', 1);
        $enable_a11y   = (bool) $this->params->get('enable_accessibility', 0);

        if (!$enable_cookie && !$enable_a11y) {
            return;
        }

        $scripts = $this->buildBannerScripts($enable_cookie, $enable_a11y);

        $body = $app->getBody();
        $body = str_replace('</body>', $scripts . "\n</body>", $body);
        $app->setBody($body);
    }

    // =========================================================================
    // Script Builders
    // =========================================================================

    private function getSiteId(): string
    {
        $site_id = trim((string) $this->params->get('site_id', ''));
        if (!empty($site_id)) {
            return htmlspecialchars($site_id, ENT_QUOTES, 'UTF-8');
        }

        $uri    = \Joomla\CMS\Uri\Uri::getInstance();
        $host   = preg_replace('/^www\./', '', $uri->getHost());
        return strtolower(str_replace('.', '-', $host));
    }

    private function buildBlockerTag(): string
    {
        $site_id = $this->getSiteId();
        $api     = self::API_BASE;

        // Kein async/defer – synchron laden ist Pflicht für den Blocker
        // data-cfasync="false" → Cloudflare Rocket Loader überspringen
        return '<script src="' . $api . '/public/cookie-blocker.js"'
             . ' data-site-id="' . $site_id . '"'
             . ' data-cfasync="false"'
             . '></script>';
    }

    private function buildBannerScripts(bool $enable_cookie, bool $enable_a11y): string
    {
        $site_id    = $this->getSiteId();
        $api        = self::API_BASE;
        $enable_tcf = (bool) $this->params->get('enable_tcf', 0);
        $out        = "\n<!-- Complyo Compliance Widgets -->\n";

        if ($enable_cookie) {
            $tcf_attr = $enable_tcf ? ' data-tcf="true"' : '';
            $out .= '<script src="' . $api . '/api/widgets/cookie-compliance.js"'
                 . ' data-site-id="' . $site_id . '"'
                 . $tcf_attr
                 . ' data-cfasync="false"'
                 . ' async'
                 . '></script>' . "\n";
        }

        if ($enable_a11y) {
            $out .= '<script src="' . $api . '/api/widgets/accessibility.js"'
                 . ' data-site-id="' . $site_id . '"'
                 . ' data-auto-fix="true"'
                 . ' data-show-toolbar="true"'
                 . ' data-cfasync="false"'
                 . ' async'
                 . '></script>' . "\n";
        }

        $out .= "<!-- End Complyo Compliance Widgets -->";
        return $out;
    }
}
