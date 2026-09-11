"""Die Sitzung endete nach 15 Minuten, und niemand hatte es gemessen.

Drei Stellen nannten drei Laufzeiten: auth_service 15 Minuten (der Wert, der
im Token steht), auth_routes 60 (nur fuers Cookie), auth.config.ts 60 (das,
was das Dashboard fuer gueltig hielt). Verlaengern konnte keiner: das
Refresh-Cookie kommt nie im Browser an, weil die Anmeldung ueber den
Dashboard-Server laeuft. Gefunden am 11.09.2026 beim Durchklicken: mitten im
Test war die Sitzung weg.

Seit demselben Tag verlaengert der Dashboard-Server das Token selbst, mit
Sperre je Refresh-Token (lib/token-erneuerung.ts, Tests dort per
`npm run test:token`). Diese Tests halten fest, dass alle Stellen denselben
Wert tragen und die Verlaengerung verdrahtet bleibt.
"""
import os
import re

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
WURZEL = os.path.abspath(os.path.join(BACKEND, '..'))


def _lies(*teile):
    with open(os.path.join(WURZEL, *teile), encoding='utf-8') as f:
        return f.read()


def test_compose_reicht_die_laufzeit_an_beide_dienste():
    """Backend UND Dashboard lesen dieselbe Variable; beide brauchen sie."""
    compose = _lies('docker-compose.yml')
    treffer = re.findall(r"ACCESS_TOKEN_EXPIRE_MINUTES=\$\{ACCESS_TOKEN_EXPIRE_MINUTES:-(\d+)\}", compose)
    assert len(treffer) == 2, treffer
    assert set(treffer) == {"480"}


def test_dashboard_nimmt_dieselbe_laufzeit_an():
    cfg = _lies('dashboard-react', 'src', 'auth.config.ts')
    m = re.search(r"Number\(process\.env\.ACCESS_TOKEN_EXPIRE_MINUTES \|\| (\d+)\) \* 60 \* 1000", cfg)
    assert m and int(m.group(1)) == 480
    assert "60 * 60 * 1000" not in cfg
    refresh = _lies('dashboard-react', 'src', 'lib', 'auth-refresh.ts')
    assert "480 * 60 * 1000" in refresh


def test_backend_standards_stimmen_ueberein():
    """Ohne Umgebungsvariable muessen auth_service und auth_routes denselben
    Standard nennen; vorher 15 gegen 60."""
    service = _lies('backend', 'auth_service.py')
    routes = _lies('backend', 'auth_routes.py')
    s = set(re.findall(r'ACCESS_TOKEN_EXPIRE_MINUTES", "(\d+)"', service))
    r = set(re.findall(r'ACCESS_TOKEN_EXPIRE_MINUTES", "(\d+)"', routes))
    assert s and s == r, (s, r)


def test_dashboard_verlaengert_serverseitig_mit_sperre():
    """Der jwt-Rueckruf ruft die gesperrte Verlaengerung auf; der Client holt
    sich das neue Token ueber die Sitzung, nicht nur ueber das Cookie, das ihn
    nie erreicht; und die Refresh-Route drosselt nicht schon den elften Kunden
    derselben Minute, denn alle kommen von der Adresse des Dashboard-Servers."""
    cfg = _lies('dashboard-react', 'src', 'auth.config.ts')
    assert "erneuereToken(" in cfg
    assert 'token.error = "RefreshAccessTokenError"' in cfg
    helfer = _lies('dashboard-react', 'src', 'lib', 'token-erneuerung.ts')
    assert "laufende = new Map" in helfer and "erledigte = new Map" in helfer
    client = _lies('dashboard-react', 'src', 'lib', 'auth-refresh.ts')
    assert client.index("getSession()") < client.index("refresh-cookie")
    routes = _lies('backend', 'auth_routes.py')
    block = routes[routes.index('@router.post("/refresh", response_model=RefreshResponse)'):]
    assert '@limiter.limit("60/minute")' in block[:700]
    paket = _lies('dashboard-react', 'package.json')
    assert '"test:token"' in paket
