"""
Was als Passwort durchgeht.

Anlass (Prüfung 10.09.2026): `RegisterRequest.password` war ein blankes `str`.
Ein einzelnes Zeichen wurde angenommen, gehasht und war ab da ein gültiges
Konto. Der Passwortwechsel in user_routes verlangte acht Zeichen — zwei
Stellen, zwei Meinungen, und die schwächere stand am Eingang.

Die Regel folgt NIST SP 800-63B, nicht der alten BSI-Schule:

- **Länge trägt, nicht Zeichenklassen.** "Sonderzeichen Pflicht" erzeugt
  `Sommer2026!` — zwölf Zeichen, vier Klassen, in jeder Wörterbuchliste. Wer
  stattdessen `pferd wagen keller lampe` nimmt, hat mehr Entropie und kann es
  sich merken. Deshalb: mindestens 12 Zeichen, keine Klassenpflicht.
- **Sperrliste statt Komplexität.** Geprüft wird gegen die Passwörter, die in
  echten Angriffen zuerst probiert werden.
- **Zusammenhang zählt.** Der eigene Name, der Teil vor dem @ der eigenen
  E-Mail und "complyo" sind für einen Angreifer, der genau dieses Konto
  angeht, keine Geheimnisse.
- **Obergrenze 128 Zeichen.** bcrypt schneidet nach 72 Byte ab; ein längeres
  Passwort wiegt den Nutzer in Sicherheit, die er nicht hat. Abgewiesen wird
  erst weit darüber, damit Passwortmanager-Ausgaben durchgehen.

Kein Ablaufdatum und kein erzwungener Wechsel: beides führt nachweislich zu
`Sommer2026!` → `Herbst2026!` und verschlechtert die Lage.
"""

import re
import unicodedata
from typing import Optional

MIN_LAENGE = 12
MAX_LAENGE = 128


class PasswortSchwach(ValueError):
    """
    Das Passwort erfüllt die Richtlinie nicht.

    Der Text dieser Ausnahme ist als einziger im Projekt dafür gedacht,
    unverändert beim Nutzer anzukommen — er sagt, was zu ändern ist. Damit das
    nicht mit einem durchgereichten internen Fehler verwechselt wird (und
    damit der Wächter in tests/test_hardening_limits_leaks.py nicht
    stumpf wird), wird er über `nutzertext` abgeholt und nie über `str(e)`.
    """

    @property
    def nutzertext(self) -> str:
        return str(self)


# Die Spitze der einschlägigen Listen (rockyou, HIBP, dazu die deutschen
# Klassiker). Bewusst kurz gehalten und im Code sichtbar statt als 200-MB-Datei
# im Image: die ersten paar hundert decken den ganz überwiegenden Teil der
# Treffer ab, alles darunter fängt die Längenregel.
_SPERRLISTE = frozenset("""
123456 123456789 12345678 password qwerty 12345 123456789 qwerty123 1q2w3e
111111 1234567890 1234567 abc123 password1 1234 qwertyuiop 123123 000000
iloveyou monkey dragon letmein football princess sunshine master welcome
shadow ashley qazwsx michael superman 696969 123qwe zxcvbnm trustno1
passwort passwort1 passwort123 hallo hallo123 schatz schatz1 sommer sommer1
winter winter1 fussball fussball1 deutschland germany berlin muenchen hamburg
arschloch scheisse ficken hurensohn schalke bayern borussia dortmund
lieblich blume blumen sonne mond sterne engel teufel himmel wolke
admin administrator root toor guest test test123 test1234 demo demo123
willkommen willkommen1 geheim geheim1 privat intern service kennwort
computer internet samsung apple google facebook amazon paypal netflix
starwars pokemon minecraft fortnite baseball basketball soccer hockey
jennifer jessica charlie thomas robert daniel matthew andrew joshua
sophie marie julia laura lisa anna maria hannah emma mia lena leonie
asdfgh asdf1234 qwer1234 1qaz2wsx zaq12wsx qwertz qwertz123 yxcvbnm
letmein1 changeme secret default temp temporary pass passwd
abcdefgh abcd1234 11111111 22222222 aaaaaaaa qwerty12 987654321
""".split())

# Tastaturreihen in beide Richtungen. `qwertzuiop` steht nicht in der Liste
# oben, ist aber genauso das Erste, was jemand probiert.
_REIHEN = (
    "qwertzuiopasdfghjklyxcvbnm",
    "qwertyuiopasdfghjklzxcvbnm",
    "1234567890",
    "abcdefghijklmnopqrstuvwxyz",
)


def _normalisiere(passwort: str) -> str:
    """NFKC, damit optisch gleiche Eingaben gleich behandelt werden."""
    return unicodedata.normalize("NFKC", passwort)


# Anteil des Passworts, der aus einer einzigen Reihe bestehen darf, bevor es
# als abgelesen gilt. Bei 0,7 faellt `1234567890123` durch (zehn von dreizehn
# Zeichen sind eine Reihe), waehrend `pferd1234` durchgeht — dort sind die
# Ziffern nur ein Anhaengsel an etwas, das keine Reihe ist.
_REIHENANTEIL = 0.7


def _laengste_reihe(kandidat: str) -> int:
    """
    Laenge des laengsten Stuecks, das auf der Tastatur nebeneinander liegt —
    vorwaerts wie rueckwaerts.

    Erste Fassung verglich `passwort in reihe`. Das fand nur Passwoerter, die
    KUERZER als die Reihe selbst sind: `1234567890123` rutschte durch, weil es
    laenger ist als `1234567890`. Gemessen wird deshalb der laengste
    zusammenhaengende Lauf, nicht die Zugehoerigkeit im Ganzen.
    """
    klein = kandidat.lower()

    def benachbart(a: str, b: str) -> bool:
        for reihe in _REIHEN:
            i, j = reihe.find(a), reihe.find(b)
            if i >= 0 and j >= 0 and abs(i - j) == 1:
                return True
        return False

    laengste = 1
    lauf = 1
    for vorher, jetzt in zip(klein, klein[1:]):
        lauf = lauf + 1 if benachbart(vorher, jetzt) else 1
        laengste = max(laengste, lauf)
    return laengste


def _ist_reihe(kandidat: str) -> bool:
    """`123456`, `abcdef`, `qwertz` — vorwärts wie rückwärts."""
    if len(kandidat) < 4:
        return False
    return _laengste_reihe(kandidat) >= max(6, int(len(kandidat) * _REIHENANTEIL))


def _ist_wiederholung(kandidat: str) -> bool:
    """
    `aaaaaaaaaaaa` oder `abcabcabcabc` — lang, aber ein einziger Baustein.

    Der Kniff: eine Zeichenkette ist genau dann die Wiederholung eines
    kürzeren Bausteins, wenn sie in ihrer eigenen Verdopplung ohne das erste
    und letzte Zeichen wieder auftaucht.
    """
    if len(kandidat) < 2:
        return False
    return kandidat in (kandidat + kandidat)[1:-1]


def _zusammenhang(email: Optional[str], name: Optional[str]) -> list:
    """Wörter, die für genau dieses Konto kein Geheimnis sind."""
    teile = ["complyo"]
    if email:
        lokal = email.split("@")[0]
        teile.append(lokal)
        # `max.mustermann` liefert auch `max` und `mustermann`
        teile.extend(t for t in re.split(r"[._\-+]", lokal) if len(t) >= 4)
    if name:
        teile.extend(t for t in re.split(r"\s+", name) if len(t) >= 4)
    return [t.lower() for t in teile if len(t) >= 4]


def pruefe(passwort: str, email: Optional[str] = None, name: Optional[str] = None) -> None:
    """
    Prüft ein Passwort. Kehrt still zurück, wenn es taugt, sonst
    `PasswortSchwach` mit einer Meldung, die dem Nutzer sagt, was zu ändern ist.

    `email` und `name` sind optional, sollten aber überall mitgegeben werden,
    wo sie bekannt sind — sie sind die einzige Prüfung, die den konkreten
    Angriff auf dieses eine Konto abdeckt.
    """
    if passwort is None:
        raise PasswortSchwach("Bitte ein Passwort angeben.")

    roh = _normalisiere(passwort)

    if roh != roh.strip():
        # Führende oder folgende Leerzeichen überleben Copy-Paste nicht
        # zuverlässig. Lieber jetzt abweisen als beim nächsten Anmelden raten.
        raise PasswortSchwach(
            "Das Passwort beginnt oder endet mit einem Leerzeichen. Bitte ohne."
        )

    if len(roh) < MIN_LAENGE:
        raise PasswortSchwach(
            f"Das Passwort ist zu kurz. Bitte mindestens {MIN_LAENGE} Zeichen — "
            "vier zufällige Wörter hintereinander sind sicherer und leichter zu "
            "merken als ein kurzes mit Sonderzeichen."
        )

    if len(roh) > MAX_LAENGE:
        raise PasswortSchwach(
            f"Das Passwort ist länger als {MAX_LAENGE} Zeichen. Bitte kürzen."
        )

    klein = roh.lower()

    if klein in _SPERRLISTE:
        raise PasswortSchwach(
            "Dieses Passwort steht auf den Listen, die bei Angriffen zuerst "
            "durchprobiert werden. Bitte ein anderes."
        )

    # `passwort123`, `hallo2026`: Sperrlisten-Wort plus angehängte Ziffern.
    kern = re.sub(r"[0-9!?.\-_#*$]+$", "", klein)
    if kern and kern in _SPERRLISTE:
        raise PasswortSchwach(
            "Das ist ein sehr verbreitetes Passwort mit angehängten Ziffern. "
            "Angreifer probieren genau diese Abwandlungen zuerst."
        )

    if _ist_reihe(roh):
        raise PasswortSchwach(
            "Das Passwort ist eine Tastatur- oder Zahlenreihe. Bitte etwas, das "
            "sich nicht auf der Tastatur ablesen lässt."
        )

    if _ist_wiederholung(roh):
        raise PasswortSchwach(
            "Das Passwort ist eine Wiederholung derselben Zeichenfolge. Länge "
            "hilft nur, wenn sie neuen Inhalt bringt."
        )

    if len(set(roh)) < 5:
        raise PasswortSchwach(
            "Das Passwort besteht aus zu wenigen verschiedenen Zeichen."
        )

    for wort in _zusammenhang(email, name):
        if wort in klein:
            raise PasswortSchwach(
                f"Das Passwort enthält „{wort}“. Wer dieses Konto gezielt "
                "angreift, kennt das bereits."
            )
