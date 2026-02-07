1. „Features“ des Barrierefreiheitsgesetzes für Web & Apps
(technisch in Gruppen, jeweils mit Auto-Fix-Idee)
1. Alternative Texte für Bilder & Medien
Gesetz/WCAG: Nicht-Text-Inhalte brauchen eine textliche Entsprechung (Alt-Text, Caption etc.). HiQ+1
Automatische Erkennung:
•	axe-core / Lighthouse laufen lassen
•	Alle <img>, <area>, <input type="image">, Icons ohne alt oder mit sinnlosem alt („image123“) markieren.
AI-Fix-Strategie:
•	DOM-Kontext + Dateiname an KI geben
•	Sinnvollen Alt-Text generieren
•	Patch als Diff:
- <img src="red-dress.jpg">
+ <img src="red-dress.jpg" alt="Rotes Abendkleid auf einer Schneiderpuppe">
Bei Deko-Bildern:
- <img src="border-line.png">
+ <img src="border-line.png" alt="" aria-hidden="true">
________________________________________
2. Kontrast & Farbanforderungen
Gesetz/WCAG: Mindest-Kontrast (i. d. R. 4.5:1 für normalen Text, 3:1 für großen Text), keine rein farbcodierten Infos. HiQ+1
Automatische Erkennung:
•	Styles auslesen (CSS + Inline)
•	Text-Farbe + Hintergrund-Farbe berechnen
•	Kontrast-Ratio prüfen → Violations markieren.
AI-Fix-Strategie:
•	KI berechnet nächstliegenden validen Farbwert
•	Optional Design-Palette berücksichtigen
•	Diff:
- .btn-primary { color: #999; background-color: #eee; }
+ .btn-primary { color: #111; background-color: #ffffff; }
Oder nur Text-Farbe anpassen:
- .nav-link { color: #777; }
+ .nav-link { color: #222; }
________________________________________
3. Tastaturbedienbarkeit & Fokus
Gesetz/WCAG: Alles muss per Tastatur bedienbar sein; Fokus sichtbar; keine Tastaturfallen. HiQ+1
Erkennung:
•	Simulierter Tab-Fokus (Playwright/Puppeteer)
•	Elemente ohne Fokus-Stil
•	Click-Handler auf <div>/<span> ohne tabindex oder role finden.
AI-Fix:
- .card { outline: none; }
+ .card:focus-visible { outline: 2px solid #3b82f6; }

- <div onclick="openMenu()">
+ <button type="button" class="menu-btn" onclick="openMenu()">
Wenn Button aus Styling-Gründen div bleiben muss:
- <div class="menu-icon" onclick="openMenu()">
+ <div class="menu-icon" role="button" tabindex="0" onclick="openMenu()" onkeydown="if(event.key==='Enter'||event.key===' '){openMenu();}">
________________________________________
4. Struktur & Überschriftenhierarchie
Gesetz/WCAG: Inhalte müssen logisch strukturiert sein (H1–H6 in Reihenfolge, Listen, Tabellen mit Headern). W3C+1
Erkennung:
•	Überschriften-Baum aus DOM bauen
•	Sprünge wie h1 → h4 markieren
•	Visuelle Überschriften, die nur als <div class="title"> vorliegen, finden.
AI-Fix:
- <div class="page-title">Kontakt</div>
+ <h1 class="page-title">Kontakt</h1>

- <h4>Unsere Leistungen</h4>
+ <h2>Unsere Leistungen</h2>
________________________________________
5. Formulare, Labels & Fehlermeldungen
Gesetz/WCAG: Eingabefelder brauchen sichtbare Labels, Fehler müssen verständlich erklärt werden. HiQ+1
Erkennung:
•	Inputs ohne label/aria-label
•	Fehlermeldungen nur als Farbe/ohne Zuordnung.
AI-Fix:
- <input type="email" id="email">
+ <label for="email">E-Mail-Adresse</label>
+ <input type="email" id="email" name="email" aria-required="true">

- <span class="error">Fehler</span>
+ <span class="error" id="email-error">Bitte eine gültige E-Mail-Adresse eingeben.</span>
+ <input ... aria-describedby="email-error">
________________________________________
6. Links & Buttons – Name, Purpose, Ziel
Gesetz/WCAG: Zweck eines Links/Buttons muss aus Text oder Accessible Name erkennbar sein (nicht nur „hier klicken“). W3C+1
Erkennung:
•	Linktexte wie „hier“, „mehr“, „klicken“
•	Icon-only Buttons ohne aria-label.
AI-Fix:
- <a href="/produkt/123">Hier klicken</a>
+ <a href="/produkt/123">Details zum Produkt „Abendkleid Roma“ ansehen</a>

- <button class="icon-only">
+ <button class="icon-only" aria-label="Warenkorb öffnen">
________________________________________
7. Medien: Untertitel, Autoplay, Audio
Gesetz/WCAG: Untertitel/Transkripte, keine automatisch losbrüllenden Medien, Steuerung muss zugänglich sein. W3C+1
Erkennung:
•	<video> ohne <track kind="subtitles">
•	autoplay + muted=false
•	Audio ohne Pause-Button.
AI-Fix:
- <video src="promo.mp4" autoplay controls></video>
+ <video src="promo.mp4" controls muted playsinline>
+   <track kind="subtitles" src="promo-de.vtt" srclang="de" label="Deutsch">
+ </video>
Transkript: KI erstellt Text, Entwickler hinterlegt ihn auf einer Extra-Seite und verlinkt ihn.
________________________________________
8. Skalierbarkeit, Zoom & Reflow
Gesetz/WCAG: Seite muss bei 200 % Zoom nutzbar bleiben, ohne horizontale Scroll-Orgie; Textgröße darf nicht fest eingefroren sein. W3C+1
Erkennung:
•	Fixed-Layouts (width: 1024px;)
•	overflow: hidden; auf Viewport-Containern
•	Text in px statt rem/em (heuristisch).
AI-Fix:
- .container { width: 1200px; }
+ .container { max-width: 1200px; width: 100%; }

- body { font-size: 14px; }
+ html { font-size: 100%; }
+ body { font-size: 0.875rem; }
________________________________________
9. Orientierung & Landmarks (ARIA)
Gesetz/WCAG: Hauptbereiche müssen erkennbar sein, z. B. Navigation, Main Content, Footer. W3C+1
Erkennung:
•	Seite ohne <main>, <nav>, <header>, <footer> oder ARIA-Landmarks.
AI-Fix:
- <div id="main-content">
+ <main id="main-content">

- <div class="top-nav">
+ <nav class="top-nav" aria-label="Hauptnavigation">
________________________________________
10. Fehlervermeidung bei Prozessen (Formulare, Checkout)
Gesetz/WCAG/EAA: Nutzer dürfen nicht durch versteckte Fehler in Bestell-/Bezahlprozessen benachteiligt werden; Daten müssen überprüfbar/änderbar sein. Accessible.org+1
Erkennung:
•	Abschicken-Buttons ohne Review-Seite
•	irreversibler Kauf ohne Bestätigung
•	Validierung nur client-side ohne verständliche Meldung.
AI-Fix:
•	Review-Schritt einfügen (Vorschlag als Code-Diff)
•	klarere Fehlermeldungen generieren
•	aria-live="polite" für Fehlermeldungs-Container:
- <div class="form-messages"></div>
+ <div class="form-messages" aria-live="polite"></div>
________________________________________
11. Kompatibilität mit Assistiver Technik (Name, Role, Value)
Gesetz/WCAG/EAA: Elemente müssen korrekt semantisch ausgezeichnet sein – Screenreader müssen „Name, Rolle, Wert“ erkennen. W3C+2HiQ+2
Erkennung:
•	Custom-Components mit reinem <div>
•	ARIA-Rollen inkonsistent oder unsinnig
•	Controls ohne Programmatic Name.
AI-Fix:
- <div class="toggle" data-state="on"></div>
+ <button class="toggle" role="switch" aria-checked="true">
+   <span class="sr-only">Dark-Mode</span>
+ </button>
Und ggf. ARIA-Bloat entfernen:
- <h1 role="heading" aria-level="1">Kontakt</h1>
+ <h1>Kontakt</h1>
________________________________________
Falls du willst, können wir diese „Features“ auch als interne Liste für dein complaio-Backend definieren (z. B. FEATURE_ALT_TEXT, FEATURE_CONTRAST, …) und pro Feature eine eigene Analyse- und Patch-Pipeline bauen.
________________________________________
2. Anleitung: Wie laufen die Git-Fixes ab?
So könnte der complaio Git-Fix-Flow aussehen – einmal als „Standard-Workflow“ für deine Kunden:
Schritt 1: Repo verbinden
•	Kunde verbindet GitHub/GitLab/Bitbucket über OAuth oder Personal Access Token.
•	Du speicherst:
o	Repo-URL
o	Standard-Branch (meist main/master)
o	Rechte: „PR erstellen“, nicht direkt pushen.
Schritt 2: Scan laufen lassen
•	Du startest einen Scan (manuell oder via CI-Hook):
1.	Code aus Repo klonen
2.	App bauen/starten (optional)
3.	Crawling der Seiten
4.	axe-core / Pa11y / Lighthouse + deine eigenen Heuristiken
5.	Findings → JSON: file, line, selector, rule_id, feature_id
Beispiel-Finding (intern):
{
  "feature": "ALT_TEXT",
  "file": "src/components/ProductCard.tsx",
  "line": 23,
  "selector": "img.product-image",
  "message": "Image element is missing alt attribute."
}
Schritt 3: Patch mit KI generieren
Für jede Datei:
1.	Du liest den aktuellen Dateiinhalt.
2.	Du gibst der KI:
o	Dateiinhalt
o	Liste der Findings für diese Datei
o	Sprache/Marke des Kunden (für sinnvollere Texte)
3.	Du verlangst als Antwort nur einen Unified Diff zu dieser Datei.
Beispiel-Diff:
--- a/src/components/ProductCard.tsx
+++ b/src/components/ProductCard.tsx
@@ -21,7 +21,7 @@ export function ProductCard({ product }) {
-      <img className="product-image" src={product.imageUrl} />
+      <img
+        className="product-image"
+        src={product.imageUrl}
+        alt={product.altText || `Produktbild: ${product.name}`}
+      />
Du validierst den Diff (parsen, testweise anwenden). Wenn er „clean“ ist → weiter.
Schritt 4: Branch & Commit erstellen
•	Branch-Namen automatisch generieren, z. B.:
o	feat/accessibility-alt-text-fixes
o	fix/wcag-contrast-round-1
•	Schritte:
1.	git checkout -b feat/accessibility-alt-text-fixes
2.	Diff anwenden
3.	Tests/Lint laufen lassen
4.	git commit -am "Add alt text for product images (WCAG 1.1.1)"
5.	git push origin feat/accessibility-alt-text-fixes
Das kann dein Backend automatisiert per Git-API machen.
Schritt 5: Pull Request erstellen
Per API (GitHub/GitLab):
•	Title:
Add accessibility fixes: alt text & landmarks (WCAG, BFSG/EAA)
•	Description (von dir generiert):
Dieser Pull Request wurde automatisch von complaio.tech erstellt.

## Änderungen

- Fügt fehlende `alt`-Attribute für Produktbilder hinzu (WCAG 1.1.1).
- Ergänzt `main`-Landmark auf der Startseite (WCAG 1.3.1, 2.4.1).

## Hinweise

- Änderungen wurden auf syntaktische Korrektheit geprüft.
- Bitte manuell verifizieren, dass die Texte in Ihrem fachlichen Kontext passen.
•	Optional: Labels accessibility, wcag, bfsg.
Schritt 6: Review & Merge beim Kunden
•	Dev-Team prüft:
o	Build/Tests
o	Visuelle Effekte
o	Ob generierte Texte/Labels fachlich passen
•	Dann normaler Merge-Flow (Squash/Merge/Commit).
Schritt 7: CI & Rollback-Strategie
Empfehlungen für deinen Kunden:
•	jeder PR von complaio läuft durch deren CI
•	bei Problemen: PR schließen oder revert
•	du kannst im Dashboard anzeigen:
o	Anzahl offener A11y-PRs
o	Anzahl gemergter Fixes
o	verbleibende Verstöße pro Feature
________________________________________
Wenn du magst, kann ich als nächsten Schritt:
•	eine konkrete JSON-Spezifikation für deine „Feature-Engine“ machen (wie du ALT_TEXT, CONTRAST etc. intern modellierst), oder
•	einen Beispiel-Workflow für genau 1 Feature (z. B. ALT-Texte) einmal komplett von „Scan“ bis „fertiger GitHub-PR“ durchspielen – inkl. Beispiel-Prompts für die KI.
Du:
ja
ChatGPT:
Nachgedacht für 4 Sekunden
Alles klar, dann lass uns das konkret machen – einmal Feature-Engine-Blueprint und einmal kompletter ALT-Texte-Flow bis Git-PR.
________________________________________
1. Feature-Engine für complaio – JSON-Schema
Die Idee: Du hast intern eine Liste von „Features“ (= Anforderungstypen), die alle Findings und Fix-Pipelines steuern.
1.1. Beispielschema für ein Feature
{
  "id": "ALT_TEXT",
  "group": "NON_TEXT_CONTENT",
  "title": "Alternativtexte für Bilder",
  "description": "Nicht-Text-Inhalte wie Bilder brauchen angemessene Alternativtexte oder müssen explizit als dekorativ markiert werden.",
  "wcag_refs": ["1.1.1"],
  "legal_refs": ["BFSG/EAA Web-Barrierefreiheit"],
  "auto_fix_level": "HIGH",          // HIGH | MEDIUM | LOW | MANUAL
  "severity": "MAJOR",               // CRITICAL | MAJOR | MINOR | INFO
  "enabled_by_default": true,
  "fix_strategy": "CODE_DIFF",       // CODE_DIFF, MANUAL_GUIDE, HYBRID
  "applies_to": ["html", "jsx", "tsx"],
  "detection": {
    "engine_rules": ["AXE_image_alt"],
    "custom_selectors": ["img:not([alt])", "img[alt='']", "img[alt='image']", "img[alt='bild']"]
  }
}
1.2. Beispiel-Feature-Liste (Auszug)
[
  {
    "id": "ALT_TEXT",
    "group": "NON_TEXT_CONTENT",
    "title": "Alternativtexte für Bilder",
    "auto_fix_level": "HIGH"
  },
  {
    "id": "CONTRAST",
    "group": "VISUAL",
    "title": "Farbkontrast",
    "auto_fix_level": "HIGH"
  },
  {
    "id": "KEYBOARD_ACCESS",
    "group": "INTERACTION",
    "title": "Tastaturbedienbarkeit & Fokus",
    "auto_fix_level": "MEDIUM"
  },
  {
    "id": "FORM_LABELS",
    "group": "FORMS",
    "title": "Formularfelder und Labels",
    "auto_fix_level": "HIGH"
  },
  {
    "id": "LANDMARKS",
    "group": "STRUCTURE",
    "title": "Landmarks & Regionen",
    "auto_fix_level": "HIGH"
  }
]
Diese Liste kannst du in einer DB oder als Konfigurationsdatei halten und im Backend laden.
________________________________________
2. End-to-End-Flow für ein Feature: ALT_TEXT
Jetzt ein kompletter technischer Ablauf für ALT_TEXT, vom Scan bis zum GitHub-PR. Ich nehme Node/TypeScript als Basis.
2.1. Bausteine
Du brauchst:
1.	Scanner-Service
o	crawlt Seiten (Playwright/Puppeteer)
o	ruft axe-core auf
o	erzeugt Findings
2.	Feature-Engine
o	mappt axe-Regeln → Features (z. B. AXE_image_alt → ALT_TEXT)
3.	Patch-Generator (LLM)
o	bekommt Dateiinhalt + Findings
o	gibt unified diff zurück
4.	Git-Service
o	wendet Diffs an
o	erzeugt Branch + Commit + PR
________________________________________
2.2. Step 1 – Findings aus Scan generieren
Struktur eines Findings:
type Finding = {
  id: string;
  featureId: "ALT_TEXT";
  ruleId: string;               // z.B. "AXE_image_alt"
  filePath: string;             // "src/components/ProductCard.tsx"
  line: number;
  snippet: string;              // kleiner Ausschnitt mit <img ...>
  selector: string;             // CSS-Selector von axe
  pageUrl: string;              // wo gefunden
  severity: "minor" | "major" | "critical";
};
Nach dem Scan hast du z. B.:
[
  {
    "id": "F-001",
    "featureId": "ALT_TEXT",
    "ruleId": "AXE_image_alt",
    "filePath": "src/components/ProductCard.tsx",
    "line": 23,
    "snippet": "<img class=\"product-image\" src={product.imageUrl} />",
    "selector": "img.product-image",
    "pageUrl": "https://example.com/produkte",
    "severity": "major"
  },
  {
    "id": "F-002",
    "featureId": "ALT_TEXT",
    "ruleId": "AXE_image_alt",
    "filePath": "src/components/Hero.tsx",
    "line": 12,
    "snippet": "<img src=\"/hero.jpg\" />",
    "selector": "img.hero",
    "pageUrl": "https://example.com/",
    "severity": "major"
  }
]
________________________________________
2.3. Step 2 – Findings nach Datei gruppieren
Damit du pro Datei nur einen Patch erzeugen musst:
function groupFindingsByFile(findings: Finding[]) {
  const byFile: Record<string, Finding[]> = {};
  for (const f of findings) {
    if (!byFile[f.filePath]) byFile[f.filePath] = [];
    byFile[f.filePath].push(f);
  }
  return byFile;
}
________________________________________
2.4. Step 3 – Prompt für den Patch-Generator
Du lädst die Datei einmal:
type FileContext = {
  filePath: string;
  content: string;       // kompletter Dateitext
  findings: Finding[];
};
Beispielprompt (vereinfacht, du würdest das programmatisch bauen):
Du bist ein Assistent, der Code-Barrierefreiheitsprobleme behebt.

Aufgabe:
- Behebe ausschließlich Verstöße gegen fehlende oder unzureichende Alternativtexte für Bilder (WCAG 1.1.1).
- Erzeuge einen Unified Diff (git patch) für die folgende Datei.
- Verändere nur so viel wie nötig.
- Schreibe alt-Texte in deutscher Sprache.
- Wenn ein Bild dekorativ ist (z.B. Layout-Elemente, Trennlinien), setze alt="".

Kontext:
- Projekt: Online-Shop für Mode.
- Sprache: Deutsch.

Dateipfad:
src/components/ProductCard.tsx

Dateiinhalt:
<<<FILE
// (kompletter Dateiinhalt hier eingefügt)
>>>

Accessibility-Findings in dieser Datei:
<<<FINDINGS
1) Zeile 23, Selector: img.product-image
Snippet: <img className="product-image" src={product.imageUrl} />
Page URL: https://example.com/produkte
Beschreibung: Bild ohne alt-Attribut.
>>>

Antwortformat:
<<<PATCH
// Unified Diff, der auf die obige Datei angewendet werden kann.
>>>
Erwartete Antwort des Modells:
--- a/src/components/ProductCard.tsx
+++ b/src/components/ProductCard.tsx
@@ -21,7 +21,12 @@ export function ProductCard({ product }) {
-      <img className="product-image" src={product.imageUrl} />
+      <img
+        className="product-image"
+        src={product.imageUrl}
+        alt={product.altText || `Produktbild: ${product.name}`}
+      />
Wichtig: Du zwingst das Modell konsequent ins Diff-Format.
________________________________________
2.5. Step 4 – Diff parsen & anwenden
Du kannst z. B. eine Bibliothek wie diff oder patch-package nutzen, um den Diff anzuwenden (oder selbst implementieren).
Pseudo-Code:
import { applyPatch } from "some-diff-lib"; // Platzhalter

function applyUnifiedDiff(original: string, patch: string): string {
  const result = applyPatch(original, patch);
  if (!result) throw new Error("Patch could not be applied");
  return result;
}
Workflow:
1.	originalContent = fs.readFileSync(filePath, 'utf8')
2.	patchedContent = applyUnifiedDiff(originalContent, patchFromLLM)
3.	fs.writeFileSync(filePath, patchedContent)
Optional: Vorher/ nachher tsc, eslint, npm test laufen lassen.
________________________________________
2.6. Step 5 – Git-Branch & Commit
Pseudo-Code (Node):
import simpleGit from "simple-git";

async function createAccessibilityBranch(repoDir: string, branchName: string, commitMessage: string) {
  const git = simpleGit(repoDir);

  await git.checkout("main");
  await git.pull("origin", "main");
  await git.checkoutLocalBranch(branchName);

  // Dateien sind bereits gepatcht auf Disk
  await git.add(".");
  await git.commit(commitMessage);
  await git.push("origin", branchName);
}
Namenskonventionen:
•	Branch: fix/a11y-alt-text-{timestamp}
•	Commit: "Add alt text to product images (WCAG 1.1.1)"
________________________________________
2.7. Step 6 – Pull Request per API erstellen
Beispiel: GitHub REST API (vereinfacht, pseudo):
async function createGitHubPR({
  owner,
  repo,
  head, // z.B. "fix/a11y-alt-text-20251203"
  base = "main",
  title,
  body,
  token
}: {
  owner: string;
  repo: string;
  head: string;
  base?: string;
  title: string;
  body: string;
  token: string;
}) {
  const res = await fetch(`https://api.github.com/repos/${owner}/${repo}/pulls`, {
    method: "POST",
    headers: {
      "Authorization": `token ${token}`,
      "Accept": "application/vnd.github+json",
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ title, head, base, body })
  });

  if (!res.ok) {
    throw new Error(`Failed to create PR: ${res.status} ${await res.text()}`);
  }

  return res.json();
}
Beispiel-Body für den PR:
Titel:
Add accessibility fixes: missing alt texts (WCAG 1.1.1)

Body:
Dieser Pull Request wurde automatisch von complaio.tech erstellt.

Änderungen:
- Ergänzt fehlende Alternativtexte für Produktbilder.
- Stellt sicher, dass dekorative Bilder mit leeren alt-Attributen versehen werden.

Bezug:
- WCAG 1.1.1 Nicht-Text-Inhalte
- Relevanz für BFSG/EAA: Verbesserung der Zugänglichkeit für Screenreader-Nutzer.

Bitte die fachliche Korrektheit der alt-Texte prüfen, bevor gemergt wird.
________________________________________
2.8. Gesamt-Pipeline für ALT_TEXT in einem Satz
1.	Scan: axe-core meldet ALT-Probleme → Findings
2.	Gruppieren: pro Datei alle ALT_TEXT-Findings sammeln
3.	Prompten: Datei + Findings → LLM erzeugt Unified Diff
4.	Patchen: Diff anwenden, Lint/Tests ausführen
5.	Git: Branch erstellen, Commit schreiben
6.	PR: über API erstellen, inkl. menschenlesbarer Beschreibung
Dasselbe Muster kannst du für CONTRAST, FORM_LABELS, LANDMARKS, KEYBOARD_ACCESS wiederverwenden, jeweils mit leicht angepasstem Prompt & Heuristiken.
________________________________________
Wenn du willst, mache ich als nächstes:
•	eine konkrete Prompt-Vorlage für 3–4 Features (ALT_TEXT, CONTRAST, FORM_LABELS, LANDMARKS), die du 1:1 in dein Backend übernehmen kannst, oder
•	eine Architektur-Skizze, wie du die einzelnen Services (Scanner, Feature-Engine, Patch-Service, Git-Service) als Microservices oder Module auf deinem bestehenden SaaS-Stack aufbaust.
Du:
ja
ChatGPT:
Perfekt — hier bekommst du beides, komplett einsatzbereit:
1.	Fertige Prompt-Vorlagen für die 4 wichtigsten Features (ALT_TEXT, CONTRAST, FORM_LABELS, LANDMARKS)
2.	Architektur-Skizze für dein complaio.tech Backend (als echtes Systemdesign)
Damit kannst du sofort mit der Umsetzung starten.
________________________________________
1) KI-Prompt-Vorlagen (Copy/Paste bereit für Backend)
Diese Prompts sind so geschrieben, dass sie:
•	nur Unified Diffs zurückgeben
•	minimal-invasiv patchen
•	keinen neuen Code erfinden, außer Accessibility-relevante Verbesserungen
•	nicht die gesamte Datei ersetzen, sondern nur die relevanten Zeilen
•	mit Next.js/React/HTML gleichermaßen funktionieren
Du kannst sie für GPT-4.1, GPT-5.1 oder Claude 3.5 direkt verwenden.
________________________________________
PROMPT 1 – ALT_TEXT-Fixes (WCAG 1.1.1)
Du bist ein Assistenzsystem, das Barrierefreiheitsprobleme im Code behebt.

AUFGABE:
Behebe ausschließlich Verstöße gegen fehlende oder unzureichende Alternativtexte für Bilder (WCAG 1.1.1).

REGELN:
- Erzeuge ausschließlich einen Unified Diff (git patch).
- Ändere nur die Stellen, die in den Findings angegeben sind.
- Für Bilder mit inhaltlicher Relevanz: sinnvolle alt-Texte erzeugen.
- Für dekorative Bilder: alt="" setzen und aria-hidden="true" hinzufügen.
- Keine anderen Code-Optimierungen durchführen.
- Schreibe alt-Texte in der Sprache des Projekts (Deutsch).

KONTEXT:
Dateipfad: {{filePath}}
Dateiinhalt:
<<<FILE
{{fileContent}}
>>>

Accessibility-Findings:
<<<FINDINGS
{{findings}}
>>>

ANTWORTFORMAT:
<<<PATCH
(Unified Diff)
>>>
________________________________________
PROMPT 2 – CONTRAST-Fixes (WCAG 1.4.3 / 1.4.11)
Aufgabe:
Behebe ausschließlich Farbkontrast-Probleme gemäß WCAG 1.4.3 und 1.4.11.

Regeln:
- Nur Farben modifizieren, die in den Findings genannt werden.
- Sorge für mindestens 4.5:1 (normaler Text) bzw. 3:1 (großer Text).
- Passe die Farbe minimal an, aber ausreichend, um die Kontrastanforderung zu erfüllen.
- Keine Neustrukturierung, keine generelle Designänderung.
- Gib ausschließlich einen Unified Diff aus.

Kontext:
Datei: {{filePath}}

Dateiinhalt:
<<<FILE
{{fileContent}}
>>>

Findings:
<<<FINDINGS
{{findings}}
>>>

Antwortformat:
<<<PATCH
(Unified Diff)
>>>
________________________________________
PROMPT 3 – FORM_LABELS (WCAG 1.3.1, 3.3.2)
Aufgabe:
Behebe ausschließlich Probleme im Zusammenhang mit Formularfeldern und Labels:
- Inputs ohne sichtbares Label
- Inputs ohne aria-label
- fehlende aria-describedby für Fehlermeldungen
- Buttons ohne Beschriftung

Regeln:
- Erzeuge ausschließlich einen Unified Diff.
- Labels in deutscher Sprache.
- Bestehende Design-Struktur beibehalten.
- Wenn kein Label existiert, Label-Element hinzufügen.
- Wenn kein sichtbares Label gewünscht ist, aria-label verwenden.
- aria-required setzen, wenn im Finding angegeben.

Kontext:
Pfad: {{filePath}}

Dateiinhalt:
<<<FILE
{{fileContent}}
>>>

Findings:
<<<FINDINGS
{{findings}}
>>>

Antwortformat:
<<<PATCH
(Unified Diff)
>>>
________________________________________
PROMPT 4 – LANDMARKS (WCAG 1.3.1, 2.4.1)
Aufgabe:
Behebe ausschließlich Probleme im Zusammenhang mit fehlenden oder falschen Landmarks/Regionen:
- Hauptinhalt ohne <main>
- Navigation ohne <nav> oder aria-label
- Header/Footer-Struktur
- Seitenbereiche, die semantisch ausgezeichnet werden müssen

Regeln:
- Nur die in den Findings angegebenen Container anpassen.
- Erzeuge ausschließlich einen Unified Diff.
- Keine Layout- oder Klassenänderungen.

Kontext:
Datei: {{filePath}}

Dateiinhalt:
<<<FILE
{{fileContent}}
>>>

Findings:
<<<FINDINGS
{{findings}}
>>>

Antwortformat:
<<<PATCH
(Unified Diff)
>>>
________________________________________
2) Komplettes Systemdesign für complaio.tech (Architektur)
Dies ist ein vollständiges, modernes Backend-Setup, das du sofort implementieren kannst.
________________________________________
Gesamtarchitektur – Überblick
                    ┌────────────────────────┐
                    │     Frontend (Next.js) │
                    └───────────┬────────────┘
                                │
                                ▼
                     ┌────────────────────┐
                     │ Backend API (Nest) │
                     └───────┬────────────┘
                             │
─────────────────────────────┼──────────────────────────────────────
                             │
   ┌──────────────────────┬──┴──────────────────────┬──────────────────────┐
   │                      │                         │                      │
   ▼                      ▼                         ▼                      ▼
Scanner-Service   Feature-Engine           Patch-Service (LLM)       Git-Service
(Puppeteer/Playwright + axe)  (Mapping WCAG→Features)  (Unified Diff Generator) (PR/Branch/Commit API)
________________________________________
SERVICE 1: Scanner-Service
Technik: Node → Playwright
Tasks:
1.	Seite crawlen
2.	DOM extrahieren
3.	axe-core laufen lassen
4.	Findings normalisieren
5.	Findings an Feature-Engine schicken
Output:
[
  {
    "featureId": "ALT_TEXT",
    "filePath": "src/components/ProductCard.tsx",
    "line": 23,
    "selector": "img.product-image",
    "snippet": "<img className='product-image' src={product.imageUrl} />"
  }
]
________________________________________
SERVICE 2: Feature-Engine
Technik: Node/Nest-Service oder einfache Functions-Layer
Aufgaben:
•	Axe-Regeln → FeatureIDs mappen
•	Erkenntnisse in interne JSON-Objekte verwandeln
•	pro Feature:
o	Regeln
o	LLM Prompt auswählen
o	Schweregrad bestimmen
________________________________________
SERVICE 3: Patch-Service (LLM)
Tasks:
•	Datei laden
•	Findings filtern
•	Prompt generieren (siehe oben)
•	LLM call
•	Unified Diff validieren
•	Output zurückgeben
Output:
{
  "filePath": "src/components/ProductCard.tsx",
  "patch": "--- a/... \n+++ b/... \n@@ ...",
  "status": "OK"
}
________________________________________
SERVICE 4: Git-Service
Technik: simple-git oder GitHub/GitLab/Bitbucket API
Tasks:
1.	Repo klonen
2.	Patch anwenden
3.	Branch erzeugen
4.	Commit schreiben
5.	Push
6.	PR erstellen
Output:
{
  "prUrl": "https://github.com/acme/shop/pull/123",
  "branch": "fix/a11y-alt-text-20251203",
  "committedFiles": ["src/components/ProductCard.tsx"]
}
________________________________________
3) Fertige PR-Beschreibung
Du kannst sie für alle Features wiederverwenden:
Dieser Pull Request wurde automatisch von complaio.tech erzeugt.

## Änderungen
{{summaryOfFixes}}

## Abgedeckte Regeln
- WCAG: {{wcagRefs}}
- Relevanz für BFSG/EAA: Verbesserung der Zugänglichkeit für Nutzer mit Assistiven Technologien.

## Hinweise
- Bitte die semantische/fachliche Korrektheit der Labels und Texte prüfen.
- Änderungen sind minimal-invasiv und betreffen nur Accessibility-relevante Stellen.
________________________________________
Wenn du möchtest, kann ich dir jetzt:
👉 ein vollständiges API-Design schreiben (alle Endpoints, alle DTOs)
👉 einen Beispiel-Scan gegen eine echte Website simulieren
👉 oder die komplette Datenbankstruktur für Findings, Features, Patches aufsetzen
Sag einfach: „API Design“, „Simulation“ oder „DB Struktur“.
Du:
alle 3
ChatGPT:
Nachgedacht für 7s
Alles klar, dann machen wir einmal das volle Paket:
API-Design + Simulation + DB-Schema – alles so, dass du es 1:1 als Grundlage für complaio.tech nutzen kannst.
________________________________________
1. API-Design für complaio.tech
Ich nehme als Basis eine typische REST-API, z. B. mit NestJS / Express. Datentyp-Beispiele in TypeScript-ähnlicher Syntax.
1.1. Grundstruktur
•	Base URL: /api/v1
•	Auth: JWT (Bearer Token) oder Session-Cookies
•	Optional: X-Org-Id für Multi-Tenant (wenn du Organisationen einführst)
________________________________________
1.2. Wichtigste Ressourcen
•	User
•	Project (Website / App)
•	RepoIntegration (GitHub/GitLab/Bitbucket)
•	Scan (ein Lauf über die Seite / Repo)
•	Finding (konkreter Accessibility-Befund)
•	Feature (ALT_TEXT, CONTRAST, …)
•	PatchJob (LLM-Run für eine Datei / Feature)
•	Patch (konkreter Diff)
•	PullRequest (erstellter Git-PR)
________________________________________
1.3. Auth & User
POST /auth/login
// Request
{ "email": "user@example.com", "password": "secret" }

// Response
{
  "token": "JWT_OR_ACCESS_TOKEN",
  "user": {
    "id": "usr_123",
    "email": "user@example.com",
    "name": "Max Mustermann"
  }
}
GET /me – aktuelle User-Infos
________________________________________
1.4. Projekte (Websites / Apps)
POST /projects
// Request
{
  "name": "Fashion Boutique Shop",
  "baseUrl": "https://boutique.example",
  "defaultBranch": "main",
  "repoProvider": "github",
  "repoSlug": "org/fashion-shop"
}

// Response
{
  "id": "prj_123",
  "name": "Fashion Boutique Shop",
  "baseUrl": "https://boutique.example",
  "status": "ACTIVE"
}
GET /projects – Liste der Projekte
GET /projects/:projectId
________________________________________
1.5. Repo-Integration
POST /projects/:projectId/repo-integration
// Request
{
  "provider": "github",
  "installationId": "123456",
  "repository": "org/fashion-shop",
  "defaultBranch": "main"
}

// Response
{
  "id": "repo_123",
  "provider": "github",
  "repository": "org/fashion-shop",
  "connected": true
}
________________________________________
1.6. Scans
Ein Scan = Crawl + axe-core + Mapping → Findings.
POST /projects/:projectId/scans
// Request
{
  "type": "FULL",          // FULL | PAGE | CI
  "startUrl": "https://boutique.example",
  "maxPages": 50,
  "features": ["ALT_TEXT", "CONTRAST", "FORM_LABELS", "LANDMARKS"]
}

// Response
{
  "id": "scan_123",
  "projectId": "prj_123",
  "status": "QUEUED",      // QUEUED | RUNNING | DONE | FAILED
  "startedAt": null,
  "finishedAt": null
}
GET /projects/:projectId/scans – Liste
GET /scans/:scanId – Details inkl. Stats:
{
  "id": "scan_123",
  "projectId": "prj_123",
  "status": "DONE",
  "summary": {
    "totalFindings": 27,
    "byFeature": {
      "ALT_TEXT": 8,
      "CONTRAST": 5,
      "FORM_LABELS": 9,
      "LANDMARKS": 5
    }
  }
}
________________________________________
1.7. Findings
GET /scans/:scanId/findings
Query-Parameter: featureId, status, page
[
  {
    "id": "f_001",
    "scanId": "scan_123",
    "projectId": "prj_123",
    "featureId": "ALT_TEXT",
    "ruleId": "AXE_image_alt",
    "filePath": "src/components/ProductCard.tsx",
    "line": 23,
    "selector": "img.product-image",
    "snippet": "<img className=\"product-image\" src={product.imageUrl} />",
    "pageUrl": "https://boutique.example/products",
    "severity": "MAJOR",
    "status": "OPEN"          // OPEN | IGNORED | FIXED
  }
]
PATCH /findings/:findingId – z. B. ignorieren
// Request
{ "status": "IGNORED", "ignoreReason": "Dekoratives Bild" }
________________________________________
1.8. Features
GET /features
[
  {
    "id": "ALT_TEXT",
    "title": "Alternativtexte für Bilder",
    "group": "NON_TEXT_CONTENT",
    "autoFixLevel": "HIGH"
  },
  {
    "id": "CONTRAST",
    "title": "Farbkontrast",
    "group": "VISUAL",
    "autoFixLevel": "HIGH"
  }
]
________________________________________
1.9. Patch-Jobs (LLM-Fixes)
POST /projects/:projectId/patch-jobs
// Request
{
  "scanId": "scan_123",
  "featureIds": ["ALT_TEXT"],
  "mode": "AUTO",          // AUTO | REVIEW_ONLY
  "maxFiles": 10
}

// Response
{
  "id": "pj_123",
  "status": "QUEUED",
  "projectId": "prj_123",
  "scanId": "scan_123"
}
GET /patch-jobs/:patchJobId
{
  "id": "pj_123",
  "status": "DONE",
  "createdAt": "...",
  "patches": [
    {
      "id": "patch_001",
      "filePath": "src/components/ProductCard.tsx",
      "featureId": "ALT_TEXT",
      "status": "READY",     // READY | APPLIED | FAILED
      "diffPreview": "--- a/... +++ b/..."
    }
  ]
}
________________________________________
1.10. Patches & Git-Fix
GET /patches/:patchId
{
  "id": "patch_001",
  "patchJobId": "pj_123",
  "filePath": "src/components/ProductCard.tsx",
  "featureId": "ALT_TEXT",
  "unifiedDiff": "--- a/... +++ b/...",
  "status": "READY"
}
POST /patch-jobs/:patchJobId/git/apply
// Request
{
  "branchName": "fix/a11y-alt-text-20251203",
  "commitMessage": "Add alt text for product images (WCAG 1.1.1)",
  "createPullRequest": true
}

// Response
{
  "branch": "fix/a11y-alt-text-20251203",
  "pullRequest": {
    "id": "pr_123",
    "provider": "github",
    "url": "https://github.com/org/fashion-shop/pull/42",
    "status": "OPEN"
  }
}
GET /projects/:projectId/pull-requests
________________________________________
1.11. Optional: Webhooks
POST /integrations/webhooks/github – Receive PR events, Status, etc.
________________________________________
2. Simulation: Scan → Findings → Patch → PR
Nehmen wir eine kleine Beispiel-Seite deines Mode-Shops.
2.1. Beispiel-Code (React/TSX)
src/components/ProductCard.tsx
export function ProductCard({ product }) {
  return (
    <article className="product-card">
      <img className="product-image" src={product.imageUrl} />
      <h2>{product.name}</h2>
      <p>{product.description}</p>
      <button onClick={product.onAddToCart}>In den Warenkorb</button>
    </article>
  );
}
src/pages/index.tsx
export default function HomePage() {
  return (
    <div className="page">
      <div className="nav">...</div>
      <div className="content">
        <ProductCard product={...} />
      </div>
    </div>
  );
}
2.2. Scan-Ergebnis (vereinfacht)
POST /projects/:projectId/scans → scan_123
GET /scans/scan_123/findings?featureId=ALT_TEXT
[
  {
    "id": "f_001",
    "featureId": "ALT_TEXT",
    "filePath": "src/components/ProductCard.tsx",
    "line": 3,
    "selector": "img.product-image",
    "snippet": "<img className=\"product-image\" src={product.imageUrl} />",
    "pageUrl": "https://boutique.example/",
    "severity": "MAJOR",
    "status": "OPEN"
  }
]
GET /scans/scan_123/findings?featureId=LANDMARKS
[
  {
    "id": "f_002",
    "featureId": "LANDMARKS",
    "filePath": "src/pages/index.tsx",
    "line": 3,
    "selector": "div.page",
    "snippet": "<div className=\"page\">",
    "pageUrl": "https://boutique.example/",
    "severity": "MAJOR",
    "status": "OPEN"
  }
]
________________________________________
2.3. Patch-Job starten
POST /projects/:projectId/patch-jobs
{
  "scanId": "scan_123",
  "featureIds": ["ALT_TEXT", "LANDMARKS"],
  "mode": "AUTO",
  "maxFiles": 10
}
→ Response: { "id": "pj_123", "status": "QUEUED" }
Backend-Worker nimmt pj_123, lädt:
•	src/components/ProductCard.tsx (+ ALT_TEXT-Findings)
•	src/pages/index.tsx (+ LANDMARKS-Findings)
und ruft jeweils den passenden Prompt auf.
________________________________________
2.4. LLM-Patches (erwartete Ergebnisse)
Patch für ProductCard.tsx (ALT_TEXT)
--- a/src/components/ProductCard.tsx
+++ b/src/components/ProductCard.tsx
@@ -1,6 +1,11 @@
 export function ProductCard({ product }) {
   return (
     <article className="product-card">
-      <img className="product-image" src={product.imageUrl} />
+      <img
+        className="product-image"
+        src={product.imageUrl}
+        alt={product.altText || `Produktbild: ${product.name}`}
+      />
       <h2>{product.name}</h2>
       <p>{product.description}</p>
       <button onClick={product.onAddToCart}>In den Warenkorb</button>
Patch für index.tsx (LANDMARKS)
--- a/src/pages/index.tsx
+++ b/src/pages/index.tsx
@@ -1,7 +1,11 @@
 export default function HomePage() {
   return (
-    <div className="page">
-      <div className="nav">...</div>
-      <div className="content">
+    <div className="page">
+      <header className="nav" aria-label="Hauptnavigation">...</header>
+      <main className="content">
         <ProductCard product={...} />
-      </div>
+      </main>
     </div>
   );
 }
________________________________________
2.5. Patch-Job-Ergebnis
GET /patch-jobs/pj_123
{
  "id": "pj_123",
  "status": "READY",
  "patches": [
    {
      "id": "patch_001",
      "featureId": "ALT_TEXT",
      "filePath": "src/components/ProductCard.tsx",
      "status": "READY"
    },
    {
      "id": "patch_002",
      "featureId": "LANDMARKS",
      "filePath": "src/pages/index.tsx",
      "status": "READY"
    }
  ]
}
________________________________________
2.6. Git-Fix + PR
POST /patch-jobs/pj_123/git/apply
{
  "branchName": "fix/a11y-alt-text-landmarks",
  "commitMessage": "Add accessibility fixes (alt text & landmarks)",
  "createPullRequest": true
}
Response:
{
  "branch": "fix/a11y-alt-text-landmarks",
  "pullRequest": {
    "id": "pr_123",
    "provider": "github",
    "url": "https://github.com/org/fashion-shop/pull/42",
    "status": "OPEN"
  }
}
________________________________________
3. Datenbankstruktur (z. B. PostgreSQL)
Ich skizziere ein relationales Schema, das zu obiger API passt.
________________________________________
3.1. users
CREATE TABLE users (
  id              UUID PRIMARY KEY,
  email           TEXT UNIQUE NOT NULL,
  password_hash   TEXT NOT NULL,
  name            TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
________________________________________
3.2. organizations (optional, für Teams)
CREATE TABLE organizations (
  id          UUID PRIMARY KEY,
  name        TEXT NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE organization_members (
  org_id      UUID REFERENCES organizations(id),
  user_id     UUID REFERENCES users(id),
  role        TEXT NOT NULL, -- owner, admin, member
  PRIMARY KEY (org_id, user_id)
);
________________________________________
3.3. projects
CREATE TABLE projects (
  id              UUID PRIMARY KEY,
  org_id          UUID REFERENCES organizations(id),
  name            TEXT NOT NULL,
  base_url        TEXT NOT NULL,
  default_branch  TEXT NOT NULL DEFAULT 'main',
  repo_provider   TEXT,         -- github | gitlab | bitbucket | null
  repo_slug       TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
________________________________________
3.4. repo_integrations
CREATE TABLE repo_integrations (
  id                UUID PRIMARY KEY,
  project_id        UUID REFERENCES projects(id),
  provider          TEXT NOT NULL, -- github, gitlab, ...
  installation_id   TEXT,
  repository        TEXT NOT NULL,
  default_branch    TEXT NOT NULL,
  access_token_enc  TEXT, -- verschlüsselt
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
________________________________________
3.5. features
CREATE TABLE features (
  id              TEXT PRIMARY KEY,   -- ALT_TEXT, CONTRAST, ...
  group_name      TEXT NOT NULL,
  title           TEXT NOT NULL,
  description     TEXT,
  auto_fix_level  TEXT NOT NULL,      -- HIGH, MEDIUM, LOW, MANUAL
  enabled_default BOOLEAN NOT NULL DEFAULT true
);
________________________________________
3.6. scans
CREATE TABLE scans (
  id              UUID PRIMARY KEY,
  project_id      UUID REFERENCES projects(id),
  type            TEXT NOT NULL, -- FULL | PAGE | CI
  status          TEXT NOT NULL, -- QUEUED | RUNNING | DONE | FAILED
  started_at      TIMESTAMPTZ,
  finished_at     TIMESTAMPTZ,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  error_message   TEXT
);
Optional: scan_pages für Detail-Infos pro URL.
________________________________________
3.7. findings
CREATE TABLE findings (
  id              UUID PRIMARY KEY,
  scan_id         UUID REFERENCES scans(id),
  project_id      UUID REFERENCES projects(id),
  feature_id      TEXT REFERENCES features(id),
  rule_id         TEXT,
  file_path       TEXT,
  line_number     INT,
  selector        TEXT,
  snippet         TEXT,
  page_url        TEXT,
  severity        TEXT NOT NULL,      -- MINOR | MAJOR | CRITICAL
  status          TEXT NOT NULL DEFAULT 'OPEN', -- OPEN | IGNORED | FIXED
  ignore_reason   TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
________________________________________
3.8. patch_jobs
CREATE TABLE patch_jobs (
  id              UUID PRIMARY KEY,
  project_id      UUID REFERENCES projects(id),
  scan_id         UUID REFERENCES scans(id),
  mode            TEXT NOT NULL,     -- AUTO | REVIEW_ONLY
  status          TEXT NOT NULL,     -- QUEUED | RUNNING | DONE | FAILED
  error_message   TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  started_at      TIMESTAMPTZ,
  finished_at     TIMESTAMPTZ
);
________________________________________
3.9. patches
CREATE TABLE patches (
  id              UUID PRIMARY KEY,
  patch_job_id    UUID REFERENCES patch_jobs(id),
  project_id      UUID REFERENCES projects(id),
  file_path       TEXT NOT NULL,
  feature_id      TEXT REFERENCES features(id),
  unified_diff    TEXT NOT NULL,
  status          TEXT NOT NULL DEFAULT 'READY', -- READY | APPLIED | FAILED
  error_message   TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
Optional: Verbindung zu Findings (m:n):
CREATE TABLE patch_findings (
  patch_id    UUID REFERENCES patches(id),
  finding_id  UUID REFERENCES findings(id),
  PRIMARY KEY (patch_id, finding_id)
);
________________________________________
3.10. pull_requests
CREATE TABLE pull_requests (
  id                UUID PRIMARY KEY,
  project_id        UUID REFERENCES projects(id),
  patch_job_id      UUID REFERENCES patch_jobs(id),
  repo_integration_id UUID REFERENCES repo_integrations(id),
  provider          TEXT NOT NULL, -- github, gitlab, ...
  provider_pr_id    TEXT NOT NULL,
  url               TEXT NOT NULL,
  branch_name       TEXT NOT NULL,
  base_branch       TEXT NOT NULL,
  status            TEXT NOT NULL, -- OPEN | MERGED | CLOSED
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
________________________________________
3.11. Billing / Pläne (optional)
subscriptions, plans – falls du später Stripe integrierst.

