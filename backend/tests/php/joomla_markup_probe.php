<?php
/**
 * Probe fuer das Joomla-Plugin ohne Joomla: die drei Klassen, die das Plugin
 * von Joomla braucht, sind hier Attrappen. Geprueft wird die echte complyo.php
 * mit der echten ComplyoMarkup.php.
 *
 * Aufruf (PHP-CLI, z. B. im Container php:8.2-cli):
 *     php backend/tests/php/joomla_markup_probe.php joomla-plugin/plg_system_complyo
 *
 * Grenze: Das ersetzt keinen Lauf in einem echten Joomla. Es beweist, dass der
 * Code fehlerfrei laedt und das Markup so umschreibt wie beschrieben.
 */

namespace Joomla\CMS\Plugin {
    class CMSPlugin
    {
        public $params;
    }
}

namespace Joomla\CMS {
    class Factory
    {
        public static $app;

        public static function getApplication()
        {
            return self::$app;
        }
    }
}

namespace Joomla\CMS\Uri {
    class Uri
    {
        public static function getInstance()
        {
            return new self();
        }

        public function getHost()
        {
            return 'www.kunde.de';
        }
    }
}

namespace {
    define('_JEXEC', 1);

    class ProbeParams
    {
        private $d;

        public function __construct(array $d)
        {
            $this->d = $d;
        }

        public function get($k, $def = null)
        {
            return array_key_exists($k, $this->d) ? $this->d[$k] : $def;
        }
    }

    class ProbeDoc
    {
        public $tags = array();

        public function addCustomTag($t)
        {
            $this->tags[] = $t;
        }
    }

    class ProbeApp
    {
        public $body = '';
        public $doc;
        public $client = 'site';

        public function isClient($c)
        {
            return $c === $this->client;
        }

        public function getDocument()
        {
            return $this->doc;
        }

        public function getBody()
        {
            return $this->body;
        }

        public function setBody($b)
        {
            $this->body = $b;
        }
    }

    $ordner = rtrim($argv[1] ?? '', '/');
    if ($ordner === '' || !is_file($ordner . '/complyo.php')) {
        fwrite(STDERR, "Plugin-Ordner fehlt\n");
        exit(2);
    }
    require $ordner . '/complyo.php';

    $fehler = 0;
    $geprueft = 0;
    function pruefe($bedingung, $was)
    {
        global $fehler, $geprueft;
        $geprueft++;
        if (!$bedingung) {
            $fehler++;
            echo "FEHLER: $was\n";
        }
    }

    function lauf(string $html, array $params = array(), string $client = 'site')
    {
        $app = new ProbeApp();
        $app->doc = new ProbeDoc();
        $app->body = $html;
        $app->client = $client;
        \Joomla\CMS\Factory::$app = $app;
        $p = new PlgSystemComplyo();
        $p->params = new ProbeParams($params);
        $p->onAfterInitialise();
        $p->onAfterRender();
        return $app;
    }

    $seite = '<!doctype html><html><head>'
        . '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        . '<link href="https://fonts.googleapis.com/css2?family=Inter&amp;display=swap" rel="stylesheet">'
        . '<script src="/media/jui/js/jquery.min.js"></script>'
        . '<script async src="https://www.googletagmanager.com/gtag/js?id=G-TEST123"></script>'
        . "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-TEST123');</script>"
        . '<script type="application/ld+json">{"@type":"Organization","name":"gtag( Kunde"}</script>'
        . '</head><body><h1>Kunde</h1>'
        . '<iframe width="560" height="315" src="https://www.youtube.com/embed/abc123" allowfullscreen></iframe>'
        . '<iframe src="https://www.google.com/maps/embed?pb=xyz"></iframe>'
        . '<iframe src="/eigene/seite.html"></iframe>'
        . '<script>var eigenes = 1; document.title = document.title;</script>'
        . '</body></html>';

    // 1) Standard: alles Fremde entschaerft, Eigenes unberuehrt
    $app = lauf($seite);
    $b = $app->body;
    pruefe(count($app->doc->tags) === 1 && strpos($app->doc->tags[0], '/public/cookie-blocker.js') !== false
        && strpos($app->doc->tags[0], 'data-site-id="kunde-de"') !== false, 'Blocker-Tag im Kopf mit abgeleiteter Site-ID');
    pruefe(!preg_match('#<script\b[^>]*\ssrc="https://www\.googletagmanager#', $b), 'gtag.js ohne scharfes src');
    pruefe(strpos($b, 'data-complyo-src="https://www.googletagmanager.com/gtag/js?id=G-TEST123"') !== false, 'gtag.js traegt data-complyo-src');
    pruefe(preg_match('#<script type="text/plain" data-complyo-consent="analytics" data-complyo-src="https://www\.googletagmanager#', $b) === 1, 'gtag.js als analytics und text/plain');
    pruefe(preg_match('#<script type="text/plain" data-complyo-consent="analytics" data-complyo-inline="1">window\.dataLayer#', $b) === 1, 'Inline-gtag entschaerft');
    pruefe(strpos($b, '<script type="application/ld+json">{"@type":"Organization","name":"gtag( Kunde"}</script>') !== false, 'JSON-LD unberuehrt');
    pruefe(strpos($b, '<script src="/media/jui/js/jquery.min.js"></script>') !== false, 'eigenes jQuery unberuehrt');
    pruefe(strpos($b, '<script>var eigenes = 1;') !== false, 'eigenes Inline-Skript unberuehrt');
    pruefe(!preg_match('#<iframe\b[^>]*\ssrc="https://www\.youtube#', $b), 'YouTube ohne scharfes src');
    pruefe(strpos($b, '<iframe data-complyo-consent="marketing" data-complyo-src="https://www.youtube.com/embed/abc123"') !== false, 'YouTube als marketing');
    pruefe(strpos($b, '<iframe data-complyo-consent="functional" data-complyo-src="https://www.google.com/maps/embed?pb=xyz"') !== false, 'Karte als functional');
    pruefe(strpos($b, '<iframe src="/eigene/seite.html">') !== false, 'eigener iframe unberuehrt');
    pruefe(!preg_match('#<link\b[^>]*\shref="https://fonts\.(googleapis|gstatic)#', $b), 'Google Fonts ohne scharfes href');
    pruefe(substr_count($b, 'data-complyo-href="https://fonts.') === 2, 'beide Font-Verweise tragen data-complyo-href');
    pruefe(strpos($b, 'data-complyo-href="https://fonts.googleapis.com/css2?family=Inter&amp;display=swap"') !== false, 'Font-Adresse korrekt maskiert');
    pruefe(preg_match('#<script src="https://api\.complyo\.de/api/widgets/cookie-compliance\.js"[^>]*async></script>\s*<!-- End Complyo Compliance Widgets -->\s*</body>#', $b) === 1, 'Banner scharf vor </body>');
    pruefe(substr_count($b, 'cookie-compliance.js') === 1, 'Banner genau einmal');

    // 2) Zweimal umschreiben aendert nichts mehr
    define('PROBE_GELADEN', 1);
    $einmal = ComplyoMarkup::rewrite($seite);
    pruefe(ComplyoMarkup::rewrite($einmal) === $einmal, 'zweiter Durchlauf aendert nichts');

    // 3) Schalter aus: Markup bleibt, Banner kommt trotzdem
    $app = lauf($seite, array('enable_markup_blocker' => 0));
    pruefe(strpos($app->body, '<script async src="https://www.googletagmanager.com/gtag/js?id=G-TEST123"></script>') !== false, 'Schalter aus: gtag.js unveraendert');
    pruefe(strpos($app->body, 'cookie-compliance.js') !== false, 'Schalter aus: Banner bleibt');

    // 4) Cookie-Banner aus: nichts anfassen
    $app = lauf($seite, array('enable_cookie_banner' => 0));
    pruefe($app->body === $seite, 'Banner aus: Seite unveraendert');
    pruefe(count($app->doc->tags) === 0, 'Banner aus: kein Blocker');

    // 5) Verwaltung: nichts anfassen
    $app = lauf($seite, array(), 'administrator');
    pruefe($app->body === $seite, 'Verwaltung: Seite unveraendert');

    // 6) Randfaelle werfen nicht
    foreach (array('', 'kein html', '<script src="https://www.googletagmanager.com/gtag/js">', str_repeat('<p>x</p>', 20000)) as $rand) {
        $app = lauf($rand);
        pruefe(is_string($app->body), 'Randfall liefert Text');
    }
    pruefe(ComplyoMarkup::rewrite(null) === null, 'null bleibt null');

    echo "$geprueft geprueft, $fehler Fehler\n";
    exit($fehler ? 1 : 0);
}
