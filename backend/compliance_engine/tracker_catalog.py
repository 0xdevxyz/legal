"""
Tracker-Katalog — Single Source of Truth für Script-/Request-Erkennung.

Konsumenten:
- automated_cookie_scanner (Script-Tag-Erkennung, re-exportiert SCRIPT_SERVICE_MAP)
- checks/cookie_check (Pre-Consent-Evidenz: Netzwerk-Requests + statischer Fallback)

Kategorien steuern die Consent-Relevanz: nur analytics/marketing sind
einwilligungspflichtiges Tracking i.S.v. TDDDG §25. functional/necessary
(Fonts, Maps, Chat, CMPs) gehören NICHT zum Pre-Consent-Check — externe
functional-Dienste behandelt der Drittlandtransfer-Check
(privacy_transfer_findings), nicht dieser Katalog.
"""

from typing import Optional, Dict, Any

# Script-URL → Dienst (Substring-Match auf lowercased URL).
# Ursprünglich in automated_cookie_scanner.py; hierher gehoben als SSOT.
SCRIPT_SERVICE_MAP: "list[tuple[str, dict]]" = [
    ("google-analytics.com/analytics.js",    {"name": "Google Analytics (UA)",  "category": "analytics",  "provider": "Google"}),
    ("google-analytics.com/ga.js",           {"name": "Google Analytics (legacy)", "category": "analytics", "provider": "Google"}),
    ("googletagmanager.com/gtm.js",          {"name": "Google Tag Manager",     "category": "analytics",  "provider": "Google"}),
    ("googletagmanager.com/gtag/js",         {"name": "Google Tag (GA4)",       "category": "analytics",  "provider": "Google"}),
    ("connect.facebook.net",                 {"name": "Meta Pixel",             "category": "marketing",  "provider": "Meta"}),
    ("static.hotjar.com",                    {"name": "Hotjar",                 "category": "analytics",  "provider": "Hotjar"}),
    ("clarity.ms/tag",                       {"name": "Microsoft Clarity",      "category": "analytics",  "provider": "Microsoft"}),
    ("bat.bing.com",                         {"name": "Microsoft Ads (UET)",    "category": "marketing",  "provider": "Microsoft"}),
    ("snap.licdn.com",                       {"name": "LinkedIn Insight Tag",   "category": "marketing",  "provider": "LinkedIn"}),
    ("ads.linkedin.com",                     {"name": "LinkedIn Ads",           "category": "marketing",  "provider": "LinkedIn"}),
    ("analytics.tiktok.com",                 {"name": "TikTok Pixel",           "category": "marketing",  "provider": "TikTok"}),
    ("sc-static.net",                        {"name": "Snapchat Pixel",         "category": "marketing",  "provider": "Snapchat"}),
    ("js.hs-scripts.com",                    {"name": "HubSpot Tracking",       "category": "analytics",  "provider": "HubSpot"}),
    ("js.hs-analytics.net",                  {"name": "HubSpot Analytics",      "category": "analytics",  "provider": "HubSpot"}),
    ("widget.intercom.io",                   {"name": "Intercom Chat",          "category": "functional", "provider": "Intercom"}),
    ("js.intercomcdn.com",                   {"name": "Intercom",               "category": "functional", "provider": "Intercom"}),
    ("cdn.segment.com",                      {"name": "Segment",                "category": "analytics",  "provider": "Segment"}),
    ("cdn.amplitude.com",                    {"name": "Amplitude",              "category": "analytics",  "provider": "Amplitude"}),
    ("cdn.mxpnl.com",                        {"name": "Mixpanel",               "category": "analytics",  "provider": "Mixpanel"}),
    ("script.hotjar.com",                    {"name": "Hotjar",                 "category": "analytics",  "provider": "Hotjar"}),
    ("cdn.logrocket.io",                     {"name": "LogRocket",              "category": "analytics",  "provider": "LogRocket"}),
    ("fullstory.com/s/fs.js",                {"name": "FullStory",              "category": "analytics",  "provider": "FullStory"}),
    ("maps.googleapis.com",                  {"name": "Google Maps",            "category": "functional", "provider": "Google"}),
    ("fonts.googleapis.com",                 {"name": "Google Fonts",           "category": "functional", "provider": "Google"}),
    ("youtube.com/embed",                    {"name": "YouTube",                "category": "marketing",  "provider": "Google"}),
    ("vimeo.com/video",                      {"name": "Vimeo",                  "category": "marketing",  "provider": "Vimeo"}),
    ("app.crisp.chat",                       {"name": "Crisp Chat",             "category": "functional", "provider": "Crisp"}),
    ("crisp.chat",                           {"name": "Crisp Chat",             "category": "functional", "provider": "Crisp"}),
    ("js.driftt.com",                        {"name": "Drift Chat",             "category": "functional", "provider": "Drift"}),
    ("cdn.cookielaw.org",                    {"name": "OneTrust CMP",           "category": "necessary",  "provider": "OneTrust"}),
    ("consent.cookiebot.com",                {"name": "Cookiebot CMP",          "category": "necessary",  "provider": "Usercentrics"}),
    # Ergänzungen (Pre-Consent-Evidenz; vorher nur teilweise in cookie_check hartcodiert)
    ("mouseflow.com",                        {"name": "Mouseflow",              "category": "analytics",  "provider": "Mouseflow"}),
    ("plausible.io/js",                      {"name": "Plausible",              "category": "analytics",  "provider": "Plausible"}),
    ("matomo.cloud",                         {"name": "Matomo (Cloud)",         "category": "analytics",  "provider": "Matomo"}),
    ("pinterest.com/v3",                     {"name": "Pinterest Tag",          "category": "marketing",  "provider": "Pinterest"}),
    ("s.pinimg.com/ct",                      {"name": "Pinterest Tag",          "category": "marketing",  "provider": "Pinterest"}),
    ("googlesyndication.com",                {"name": "Google AdSense",         "category": "marketing",  "provider": "Google"}),
    ("googleads.g.doubleclick.net",          {"name": "Google Ads",             "category": "marketing",  "provider": "Google"}),
    ("static.criteo.net",                    {"name": "Criteo",                 "category": "marketing",  "provider": "Criteo"}),
    ("cdn.taboola.com",                      {"name": "Taboola",                "category": "marketing",  "provider": "Taboola"}),
    ("widgets.outbrain.com",                 {"name": "Outbrain",               "category": "marketing",  "provider": "Outbrain"}),
]

# Endpunkte, die erst durch TATSÄCHLICHES Tracking entstehen (Collect/Pixel-Hits).
# Ein solcher Request im Netzwerk-Mitschnitt ist harte Evidenz, unabhängig davon,
# wie das Script geladen wurde.
TRACKING_COLLECT_PATTERNS: "list[tuple[str, dict]]" = [
    ("google-analytics.com/g/collect",  {"name": "Google Analytics 4 (Collect)", "category": "analytics", "provider": "Google"}),
    ("region1.google-analytics.com",    {"name": "Google Analytics 4 (Collect)", "category": "analytics", "provider": "Google"}),
    ("google-analytics.com/collect",    {"name": "Google Analytics (Collect)",   "category": "analytics", "provider": "Google"}),
    ("stats.g.doubleclick.net",         {"name": "Google Ads Remarketing",       "category": "marketing", "provider": "Google"}),
    ("facebook.com/tr",                 {"name": "Meta Pixel (Event)",           "category": "marketing", "provider": "Meta"}),
    ("linkedin.com/px",                 {"name": "LinkedIn Insight (Event)",     "category": "marketing", "provider": "LinkedIn"}),
]

# Google-Loader, die mit Consent Mode v2 (default: denied) legal VOR der
# Einwilligung geladen werden duerfen. Zaehlen deshalb NICHT als
# Netzwerk-Evidenz fuer Pre-Consent-Tracking — nur ihre Collect-Endpunkte.
CONSENT_MODE_SAFE_LOADERS = (
    "googletagmanager.com/gtag/js",
    "googletagmanager.com/gtm.js",
)

# Nicht Gegenstand des Pre-Consent-Checks: Video-Embeds und functional-Dienste
# behandelt der Drittlandtransfer-Check (Doppelmeldung vermeiden).
PRE_CONSENT_EXCLUDED = (
    "youtube.com",
    "youtube-nocookie.com",
    "vimeo.com",
)


def _consent_relevant(info: Dict[str, Any]) -> bool:
    return info.get("category") in ("analytics", "marketing")


def match_tracking_request(url: str) -> Optional[Dict[str, Any]]:
    """
    Netzwerk-Evidenz: Ordnet eine im Headless-Render beobachtete Request-URL
    einem einwilligungspflichtigen Tracker zu. Konservativ: Google-Loader mit
    Consent-Mode-Support zaehlen nicht (nur deren Collect-Endpunkte).
    """
    u = (url or "").lower()
    if not u:
        return None
    if any(ex in u for ex in PRE_CONSENT_EXCLUDED):
        return None
    for pattern, info in TRACKING_COLLECT_PATTERNS:
        if pattern in u:
            return {**info, "pattern": pattern}
    if any(loader in u for loader in CONSENT_MODE_SAFE_LOADERS):
        return None
    for pattern, info in SCRIPT_SERVICE_MAP:
        if pattern in u and _consent_relevant(info):
            return {**info, "pattern": pattern}
    return None


def match_tracking_script_src(src: str) -> Optional[Dict[str, Any]]:
    """
    Statischer Fallback (kein Render verfuegbar): Ordnet ein <script src> einem
    einwilligungspflichtigen Tracker zu. Enthaelt bewusst auch die Google-Loader
    (statisch ist Consent Mode nicht erkennbar — entspricht der Alt-Logik).
    """
    s = (src or "").lower()
    if not s:
        return None
    if any(ex in s for ex in PRE_CONSENT_EXCLUDED):
        return None
    for pattern, info in TRACKING_COLLECT_PATTERNS:
        if pattern in s:
            return {**info, "pattern": pattern}
    for pattern, info in SCRIPT_SERVICE_MAP:
        if pattern in s and _consent_relevant(info):
            return {**info, "pattern": pattern}
    return None
