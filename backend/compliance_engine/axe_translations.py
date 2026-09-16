"""
Deutsche Titel und Beschreibungen fuer axe-core-Regeln.

axe-core liefert `help` und `description` ausschliesslich auf Englisch. Bis
hierher landeten Saetze wie "All page content should be contained by landmarks"
unuebersetzt im Report einer deutschsprachigen Anwendung.

Geschluesselt wird ueber die Regel-ID (`violation.id`) — die ist stabil, waehrend
sich der Hilfetext zwischen axe-Versionen aendern kann. Unbekannte Regeln fallen
auf den englischen Originaltext zurueck; das ist haesslich, aber ehrlicher als
eine geratene Uebersetzung.
"""

# rule_id -> (titel, beschreibung)
AXE_DE: "dict[str, tuple[str, str]]" = {
    # --- Textalternativen (WCAG 1.1.1) ---
    "image-alt": (
        "Bild ohne Alt-Text",
        "Ein Bild hat kein alt-Attribut. Screenreader können den Inhalt nicht wiedergeben.",
    ),
    "input-image-alt": (
        "Bild-Button ohne Alt-Text",
        "Ein <input type=\"image\"> hat kein alt-Attribut und ist damit unbeschriftet.",
    ),
    "area-alt": (
        "Imagemap-Bereich ohne Alt-Text",
        "Ein <area>-Element einer Imagemap hat keinen alternativen Text.",
    ),
    "object-alt": (
        "Eingebettetes Objekt ohne Textalternative",
        "Ein <object>-Element hat keinen alternativen Text.",
    ),
    "role-img-alt": (
        "Grafik mit Bild-Rolle ohne Namen",
        "Ein Element mit role=\"img\" hat keinen zugänglichen Namen.",
    ),
    "image-redundant-alt": (
        "Alt-Text wiederholt danebenstehenden Text",
        "Der Alt-Text eines Bildes entspricht dem Text daneben — Screenreader lesen ihn doppelt vor.",
    ),
    "svg-img-alt": (
        "SVG-Grafik ohne Textalternative",
        "Ein SVG mit Bild-Rolle hat keinen zugänglichen Namen.",
    ),

    # --- Beschriftung von Bedienelementen (WCAG 4.1.2 / 2.4.4) ---
    "label": (
        "Formularfeld ohne Label",
        "Ein Eingabefeld hat kein zugeordnetes Label. Nutzer wissen nicht, was einzugeben ist.",
    ),
    "form-field-multiple-labels": (
        "Formularfeld mit mehreren Labels",
        "Einem Feld sind mehrere Labels zugeordnet — Screenreader geben das uneinheitlich wieder.",
    ),
    "button-name": (
        "Schaltfläche ohne Beschriftung",
        "Ein Button hat keinen erkennbaren Text und keinen zugänglichen Namen.",
    ),
    "link-name": (
        "Link ohne erkennbaren Text",
        "Ein Link hat keinen Text und keinen zugänglichen Namen — sein Ziel ist nicht erkennbar.",
    ),
    "input-button-name": (
        "Eingabe-Schaltfläche ohne Beschriftung",
        "Ein <input type=\"button|submit|reset\"> hat keinen zugänglichen Namen.",
    ),
    "select-name": (
        "Auswahlfeld ohne Beschriftung",
        "Ein <select> hat keinen zugänglichen Namen.",
    ),
    "frame-title": (
        "Frame ohne Titel",
        "Ein <iframe> hat kein title-Attribut — sein Zweck ist für Screenreader unklar.",
    ),

    # --- Struktur und Navigation ---
    "region": (
        "Inhalte außerhalb von Landmark-Bereichen",
        "Teile der Seite liegen außerhalb von <main>, <nav>, <header> und Co. "
        "Screenreader-Nutzer können nicht gezielt dorthin springen.",
    ),
    "landmark-one-main": (
        "Kein <main>-Bereich vorhanden",
        "Der Seite fehlt ein eindeutiger Hauptinhaltsbereich.",
    ),
    "landmark-unique": (
        "Mehrdeutige Landmark-Bereiche",
        "Mehrere Landmarks derselben Art sind nicht durch eigene Namen unterscheidbar.",
    ),
    "heading-order": (
        "Überschriftenebenen springen",
        "Die Überschriftenhierarchie überspringt Ebenen (z.B. h2 direkt auf h4). "
        "Die Gliederung wird dadurch unverständlich.",
    ),
    "empty-heading": (
        "Leere Überschrift",
        "Eine Überschrift enthält keinen Text.",
    ),
    "page-has-heading-one": (
        "Keine H1-Überschrift",
        "Der Seite fehlt eine Hauptüberschrift.",
    ),
    "bypass": (
        "Kein Sprunglink zum Hauptinhalt",
        "Es gibt keine Möglichkeit, wiederkehrende Navigation zu überspringen.",
    ),
    "list": (
        "Fehlerhafte Listenstruktur",
        "Eine Liste enthält andere Elemente als <li>.",
    ),
    "listitem": (
        "Listenpunkt außerhalb einer Liste",
        "Ein <li> steht nicht innerhalb von <ul> oder <ol>.",
    ),
    "definition-list": (
        "Fehlerhafte Definitionsliste",
        "Eine <dl> ist nicht korrekt aus <dt>/<dd> aufgebaut.",
    ),

    # --- Farbe und Darstellung ---
    "color-contrast": (
        "Zu geringer Farbkontrast",
        "Text hebt sich zu schwach vom Hintergrund ab (WCAG AA verlangt 4,5:1, "
        "bei großem Text 3:1).",
    ),
    "color-contrast-enhanced": (
        "Kontrast erreicht AAA-Stufe nicht",
        "Der Kontrast genügt nicht der erhöhten Anforderung von 7:1.",
    ),
    "link-in-text-block": (
        "Link nur durch Farbe erkennbar",
        "Ein Link im Fließtext ist allein an der Farbe erkennbar — für Farbfehlsichtige unsichtbar.",
    ),
    "meta-viewport": (
        "Zoom gesperrt",
        "Die viewport-Angabe verhindert das Vergrößern der Seite.",
    ),

    # --- ARIA ---
    "aria-required-attr": (
        "Pflicht-ARIA-Attribut fehlt",
        "Einem Element mit ARIA-Rolle fehlt ein für diese Rolle vorgeschriebenes Attribut.",
    ),
    "aria-required-children": (
        "ARIA-Rolle ohne erforderliche Kindelemente",
        "Eine ARIA-Rolle verlangt bestimmte Kindelemente, die fehlen.",
    ),
    "aria-required-parent": (
        "ARIA-Rolle ohne erforderliches Elternelement",
        "Eine ARIA-Rolle steht nicht im vorgeschriebenen Elternelement.",
    ),
    "aria-roles": (
        "Ungültige ARIA-Rolle",
        "Ein role-Attribut enthält einen unbekannten Wert.",
    ),
    "aria-valid-attr": (
        "Ungültiges ARIA-Attribut",
        "Ein aria-Attribut ist nicht Teil der Spezifikation.",
    ),
    "aria-valid-attr-value": (
        "Ungültiger Wert in ARIA-Attribut",
        "Ein aria-Attribut trägt einen unzulässigen Wert.",
    ),
    "aria-hidden-body": (
        "Seiteninhalt komplett vor Screenreadern verborgen",
        "Auf <body> steht aria-hidden=\"true\" — die gesamte Seite ist unzugänglich.",
    ),
    "aria-hidden-focus": (
        "Verborgenes Element ist fokussierbar",
        "Ein mit aria-hidden ausgeblendetes Element lässt sich per Tastatur anspringen.",
    ),
    "aria-allowed-attr": (
        "ARIA-Attribut für diese Rolle unzulässig",
        "Ein aria-Attribut ist für die verwendete Rolle nicht erlaubt.",
    ),
    "aria-command-name": (
        "Bedienelement ohne zugänglichen Namen",
        "Ein Element mit Button-, Link- oder Menüpunkt-Rolle hat keinen Namen.",
    ),
    "aria-input-field-name": (
        "ARIA-Eingabefeld ohne Namen",
        "Ein Eingabefeld mit ARIA-Rolle hat keinen zugänglichen Namen.",
    ),
    "aria-toggle-field-name": (
        "Schalter ohne zugänglichen Namen",
        "Ein Umschalter (Checkbox, Switch, Radio) hat keinen zugänglichen Namen.",
    ),

    # --- Sprache und Dokument ---
    "html-has-lang": (
        "Seitensprache nicht angegeben",
        "Dem <html>-Element fehlt das lang-Attribut. Screenreader wählen die falsche Aussprache.",
    ),
    "html-lang-valid": (
        "Ungültige Sprachangabe",
        "Das lang-Attribut enthält keinen gültigen Sprachcode.",
    ),
    "valid-lang": (
        "Ungültige Sprachangabe im Text",
        "Ein lang-Attribut im Seiteninhalt enthält keinen gültigen Sprachcode.",
    ),
    "document-title": (
        "Seite ohne Titel",
        "Dem Dokument fehlt ein <title>. Nutzer können Tabs nicht unterscheiden.",
    ),
    "duplicate-id-active": (
        "Doppelte ID an Bedienelementen",
        "Zwei bedienbare Elemente tragen dieselbe id — Verweise darauf werden mehrdeutig.",
    ),
    "duplicate-id-aria": (
        "Doppelte ID in ARIA-Verweis",
        "Eine per ARIA referenzierte id kommt mehrfach vor.",
    ),

    # --- Tabellen ---
    "td-headers-attr": (
        "Fehlerhafte Tabellenzuordnung",
        "Das headers-Attribut einer Zelle verweist nicht auf Kopfzellen derselben Tabelle.",
    ),
    "th-has-data-cells": (
        "Kopfzelle ohne zugehörige Daten",
        "Eine Kopfzelle beschreibt keine Datenzellen.",
    ),
    "scope-attr-valid": (
        "Ungültiges scope-Attribut",
        "Das scope-Attribut einer Tabellenzelle hat einen unzulässigen Wert.",
    ),

    # --- Medien und Bewegung ---
    "video-caption": (
        "Video ohne Untertitel",
        "Einem Video fehlt eine Untertitelspur. Gehörlose Nutzer können den Inhalt nicht erfassen.",
    ),
    "audio-caption": (
        "Audio ohne Transkript",
        "Einer Audiodatei fehlt eine Textalternative.",
    ),
    "no-autoplay-audio": (
        "Ton startet automatisch",
        "Medien spielen ohne Zutun mit Ton ab und lassen sich nicht sofort stoppen.",
    ),
    "blink": (
        "Blinkender Inhalt",
        "Die Seite enthält blinkende Inhalte — ein Risiko für Menschen mit Photosensibilität.",
    ),
    "marquee": (
        "Automatisch laufender Text",
        "Ein <marquee>-Element bewegt Text ohne Stopp-Möglichkeit.",
    ),
    "meta-refresh": (
        "Automatische Weiterleitung",
        "Die Seite lädt sich selbst neu oder leitet weiter, ohne dass Nutzer das abwenden können.",
    ),
    "tabindex": (
        "Positiver tabindex stört die Reihenfolge",
        "Ein tabindex größer 0 verändert die Tab-Reihenfolge gegenüber der visuellen Anordnung.",
    ),
    "accesskeys": (
        "Doppelte Zugriffstasten",
        "Mehrere Elemente belegen dieselbe accesskey-Taste.",
    ),
    "nested-interactive": (
        "Bedienelement im Bedienelement",
        "Ein fokussierbares Element steckt in einem anderen — Screenreader geben das unzuverlässig wieder.",
    ),
    "scrollable-region-focusable": (
        "Scrollbereich nicht per Tastatur erreichbar",
        "Ein scrollbarer Bereich lässt sich nicht mit der Tastatur ansteuern.",
    ),

    # --- Nachtrag 16.09.2026: Regeln, die bis dahin auf Englisch im Bericht
    # standen ("ARIA role should be appropriate for the element" auf
    # panoart360.de). Ueberwiegend axe-Empfehlungen. ---
    "aria-allowed-role": (
        "ARIA-Rolle passt nicht zum Element",
        "Ein Element trägt eine ARIA-Rolle, die für diesen Elementtyp nicht vorgesehen ist.",
    ),
    "aria-dialog-name": (
        "Dialog ohne Namen",
        "Ein Element mit role=\"dialog\" oder \"alertdialog\" hat keinen zugänglichen Namen.",
    ),
    "aria-meter-name": (
        "Messanzeige ohne Namen",
        "Ein Element mit role=\"meter\" hat keinen zugänglichen Namen.",
    ),
    "aria-progressbar-name": (
        "Fortschrittsanzeige ohne Namen",
        "Ein Element mit role=\"progressbar\" hat keinen zugänglichen Namen.",
    ),
    "aria-roledescription": (
        "aria-roledescription ohne passende Rolle",
        "aria-roledescription steht an einem Element ohne (implizite) Rolle und wird nicht vorgelesen.",
    ),
    "aria-text": (
        "role=\"text\" mit fokussierbarem Inhalt",
        "Ein Element mit role=\"text\" enthält fokussierbare Nachfahren; die verlieren so ihre Bedeutung.",
    ),
    "aria-tooltip-name": (
        "Tooltip ohne Namen",
        "Ein Element mit role=\"tooltip\" hat keinen zugänglichen Namen.",
    ),
    "focus-order-semantics": (
        "Fokussierbares Element ohne Bedienrolle",
        "Ein Element liegt in der Tabulator-Reihenfolge, hat aber keine Rolle, die ein Bedienelement beschreibt.",
    ),
    "focusable-content": (
        "Inhalt nicht fokussierbar",
        "Ein Element mit role=\"application\" oder ähnlichem enthält keinen fokussierbaren Inhalt.",
    ),
    "focusable-disabled": (
        "Fokussierbares Element im deaktivierten Bereich",
        "Innerhalb eines mit aria-disabled markierten Bereichs sind Elemente weiter per Tastatur erreichbar.",
    ),
    "focusable-no-name": (
        "Fokussierbares Element ohne Namen",
        "Ein per Tastatur erreichbares Element hat keinen zugänglichen Namen.",
    ),
    "frame-focusable-content": (
        "Frame mit Inhalt, aber aus der Tabulator-Reihenfolge genommen",
        "Ein <iframe> mit tabindex=\"-1\" enthält fokussierbaren Inhalt, der so nicht erreichbar ist.",
    ),
    "html-xml-lang-mismatch": (
        "lang und xml:lang widersprechen sich",
        "Das <html>-Element nennt in lang und xml:lang verschiedene Sprachen.",
    ),
    "label-title-only": (
        "Formularfeld nur über title benannt",
        "Ein Formularfeld hat nur ein title-Attribut als Beschriftung; ein sichtbares <label> fehlt.",
    ),
    "landmark-banner-is-top-level": (
        "Kopfbereich nicht auf oberster Ebene",
        "Der Banner-Landmark (<header>) steckt in einem anderen Landmark.",
    ),
    "landmark-complementary-is-top-level": (
        "Seitenleiste nicht auf oberster Ebene",
        "Der Complementary-Landmark (<aside>) steckt in einem anderen Landmark.",
    ),
    "landmark-contentinfo-is-top-level": (
        "Fußbereich nicht auf oberster Ebene",
        "Der Contentinfo-Landmark (<footer>) steckt in einem anderen Landmark.",
    ),
    "landmark-main-is-top-level": (
        "Hauptinhalt nicht auf oberster Ebene",
        "Der Main-Landmark steckt in einem anderen Landmark.",
    ),
    "landmark-no-duplicate-banner": (
        "Mehrere Kopfbereiche",
        "Die Seite hat mehr als einen Banner-Landmark.",
    ),
    "landmark-no-duplicate-contentinfo": (
        "Mehrere Fußbereiche",
        "Die Seite hat mehr als einen Contentinfo-Landmark.",
    ),
    "landmark-no-duplicate-main": (
        "Mehrere Hauptinhaltsbereiche",
        "Die Seite hat mehr als einen Main-Landmark.",
    ),
    "video-description": (
        "Video ohne Audiodeskription",
        "Ein <video> hat keine Tonspur oder Textalternative, die bildliche Informationen beschreibt.",
    ),
}


def uebersetze(rule_id: str, help_text: str, description: str) -> "tuple[str, str]":
    """
    Liefert (titel, beschreibung) auf Deutsch.

    Fuer unbekannte Regeln bleibt der englische Originaltext stehen — sichtbar
    unuebersetzt statt frei erfunden.
    """
    eintrag = AXE_DE.get((rule_id or "").strip().lower())
    if eintrag is None:
        return (help_text or rule_id or "", description or "")
    return eintrag
