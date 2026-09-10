/**
 * Wohin nach der Anmeldung.
 *
 * Wer eine Unterseite aufruft und (noch) nicht angemeldet ist, landet auf
 * /login?redirect=<Ziel>. Bis zum 11.09.2026 hat die Anmeldeseite diesen
 * Parameter nie gelesen und JEDEN auf das Dashboard geschickt. Ein Lesezeichen
 * auf /settings, ein geteilter Link auf eine Freigabe, eine abgelaufene Sitzung
 * mitten in der Arbeit — alles endete auf `/`.
 *
 * Das Ziel kommt aus der Adresszeile und damit von aussen. Ungeprueft
 * weitergereicht waere es eine offene Weiterleitung:
 * `/login?redirect=https://complyo-login.example` schickt einen frisch
 * angemeldeten Kunden auf eine fremde Seite, die aussieht wie unsere. Deshalb
 * gilt nur, was garantiert auf dieser Anwendung bleibt.
 */

import { istNurFuerGaeste } from "@/lib/oeffentliche-pfade";

// Ein Platzhalter-Ursprung, der nirgends existiert. Gegen ihn wird das Ziel
// aufgeloest; hat das Ergebnis danach einen anderen Ursprung, zeigte das Ziel
// nach draussen. Bewusst nicht window.location.origin, damit die Pruefung
// auch serverseitig dasselbe Ergebnis liefert.
const BASIS = "https://ziel.invalid";

export function sicheresZiel(roh: string | null | undefined): string {
  if (!roh) return "/";

  // Nur relative Pfade. `//fremd.example` ist fuer den Browser eine absolute
  // Adresse ohne Schema, `/\fremd.example` machen manche Browser ebenfalls
  // dazu.
  if (!roh.startsWith("/") || roh.startsWith("//") || roh.startsWith("/\\")) return "/";

  // Steuerzeichen haben in einem Pfad nichts verloren und sind der klassische
  // Weg, eine der Pruefungen oben zu umgehen.
  if (/[\u0000-\u001f\u007f]/.test(roh)) return "/";

  let url: URL;
  try {
    url = new URL(roh, BASIS);
  } catch {
    return "/";
  }
  if (url.origin !== BASIS) return "/";

  // Zurueck auf /login oder /register waere eine Schleife: die Seite sieht
  // einen Angemeldeten und schickt ihn weiter — wohin, steht dann wieder hier.
  if (istNurFuerGaeste(url.pathname)) return "/";

  return url.pathname + url.search + url.hash;
}

/** Das Ziel aus der aktuellen Adresse lesen. Nur im Browser aufrufen. */
export function zielAusAdresse(): string {
  if (typeof window === "undefined") return "/";
  return sicheresZiel(new URLSearchParams(window.location.search).get("redirect"));
}
