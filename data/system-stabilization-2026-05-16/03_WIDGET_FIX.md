# Phase 3 – Widget accessibility.js Null-Guard

**Datum:** 2026-05-16

## Beobachteter Fehler

```
Uncaught (in promise) TypeError: Cannot set properties of null (setting 'hidden')
    at accessibility.js:922
```

## Root Cause

`accessibility-v6.js`, Funktion `closePanel()`:

```javascript
// VORHER (kein Null-Guard):
closePanel() {
  this.isOpen = false;
  const panel = this.container.querySelector('.complyo-panel');
  const toggleBtn = this.container.querySelector('.complyo-toggle-btn');
  
  panel.hidden = true;          // ← crash wenn panel null
  toggleBtn.setAttribute(...);  // ← crash wenn toggleBtn null
  toggleBtn.style.display = 'flex';
}
```

Tritt auf wenn `closePanel()` aufgerufen wird bevor das DOM vollständig initialisiert ist (z.B. via Keyboard-Event oder externem Script).

## Fix

```javascript
// NACHHER (mit Null-Guard):
closePanel() {
  this.isOpen = false;
  const panel = this.container.querySelector('.complyo-panel');
  const toggleBtn = this.container.querySelector('.complyo-toggle-btn');

  if (panel) {
    panel.hidden = true;
  }
  if (toggleBtn) {
    toggleBtn.setAttribute('aria-expanded', 'false');
    toggleBtn.style.display = 'flex';
  }
}
```

**Datei:** `backend/widgets/accessibility-v6.js`

## Hinweis

Die Browser-Console zeigt `accessibility.js:922` weil der Backend-Endpoint `/api/widgets/accessibility.js?version=6` die Datei `accessibility-v6.js` ausliefert. Die Zeilennummer 922 ist daher die Zeile in der minifizierten/serverseitigen Version.
