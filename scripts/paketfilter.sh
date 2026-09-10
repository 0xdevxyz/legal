#!/usr/bin/env bash
#
# Paketfilter fuer openclaw. NICHT unbeaufsichtigt laufen lassen.
#
# STAND 11.09.2026: EINGERICHTET (Nachtschicht, Entscheidung Daniel). Nicht
# ueber dieses Skript, sondern mit denselben Regeln von Hand, plus einer, die
# hier fehlte:
#
#     ufw default deny incoming; ufw default allow outgoing
#     ufw allow 58769/tcp   # SSH
#     ufw allow 80/tcp; ufw allow 443/tcp
#     ufw allow from 172.16.0.0/12   # Docker-Bridges zum Host
#     ufw --force enable
#
# Die letzte Regel ist der Grund, warum das Skript nicht 1:1 lief: Container
# sprechen den Host ueber die Bridge-Netze (172.17 bis 172.25) an, etwa fuer
# Dienste, die auf dem Host selbst laufen. Ohne die Regel haette "deny
# incoming" genau diese Verbindungen gekappt, und zwar leise.
#
# Rueckfallnetz war `systemd-run --on-active=600 ufw disable` statt `at`, weil
# `at` nicht installiert ist und systemd-run es ohne Paket kann. Nach der
# Aktivierung geprueft: neue SSH-Verbindung, alle auf openclaw gehosteten
# Domains (complyo.de, app/api.complyo.de, 11scope.com, naturheilzentrum.online,
# zahnarztpraxis-mittweida.de, loqal-Dev), Backend-Health lokal, dann den
# Timer entfernt. Von aussen waren vorher schon nur 80, 443 und 58769
# erreichbar (IONOS-Firewall, von einem fremden Netz gemessen); der Filter ist
# die zweite Schicht fuer den Tag, an dem jemand die erste umkonfiguriert.
#
# Was ufw NICHT abdeckt: von Containern veroeffentlichte Ports (5432, 6379,
# 8000) laufen ueber die DOCKER-Kette an ufw vorbei. Die schuetzt weiterhin
# DOCKER-USER (DROP fuer ens6 auf 5432/6379/8000), siehe `iptables -S DOCKER-USER`.
#
#
# Warum es ihn braucht: der Host hat derzeit keinen eigenen Filter. Die
# ufw-Ketten sind leer, das Programm ist deinstalliert, die INPUT-Regel steht
# auf ACCEPT. Dass Postgres (0.0.0.0:5432) und Redis (0.0.0.0:6379) des
# loqal-Onboardings von aussen unerreichbar sind, haengt allein an der
# IONOS-Firewall. Eine Aenderung dort legt beide offen; Redis ohne Passwort
# ist Serveruebernahme.
#
# Warum vorsichtig: ein falscher Filter sperrt SSH aus und nimmt 25
# Kundenseiten vom Netz. Deshalb baut dieses Skript ein Sicherheitsnetz ein:
# es plant VOR dem Aktivieren einen Abschaltbefehl in 10 Minuten. Wer sich
# aussperrt, wartet zehn Minuten und ist wieder drin. Wer drin bleibt, nimmt
# den geplanten Befehl mit `atrm` wieder heraus (das Skript sagt, wie).
#
# Aufruf:
#     sudo bash paketfilter.sh pruefen     # zeigt nur, was passieren wuerde
#     sudo bash paketfilter.sh scharf      # setzt die Regeln mit Rueckfallnetz
#
set -euo pipefail

SSH_PORT="$(ss -tlnp 2>/dev/null | awk '/sshd/ {split($4,a,":"); print a[length(a)]; exit}')"
: "${SSH_PORT:=58769}"

regeln() {
    echo "  ufw default deny incoming"
    echo "  ufw default allow outgoing"
    echo "  ufw allow ${SSH_PORT}/tcp     # SSH, aus ss ausgelesen"
    echo "  ufw allow 80/tcp              # nginx"
    echo "  ufw allow 443/tcp             # nginx"
    echo "  (Docker umgeht ufw ueber die DOCKER-Kette; die Ports, die"
    echo "   Container auf 0.0.0.0 binden, bleiben davon unberuehrt."
    echo "   Der zweite, wichtigere Schritt steht unten.)"
}

case "${1:-pruefen}" in
  pruefen)
    echo "SSH-Port erkannt: ${SSH_PORT}"
    echo
    echo "Diese Regeln wuerden gesetzt:"
    regeln
    echo
    echo "Danach zusaetzlich noetig, weil Docker den Filter umgeht:"
    echo "  In den compose-Dateien der loqal-Onboarding-Container die Ports"
    echo "  von \"5432:5432\" auf \"127.0.0.1:5432:5432\" umstellen"
    echo "  (ebenso 6379 und 8000), dann neu starten. Erst das nimmt sie"
    echo "  wirklich vom Netz."
    echo
    echo "Zum Ausfuehren: sudo bash $0 scharf"
    ;;
  scharf)
    command -v ufw >/dev/null || { echo "ufw fehlt: apt install ufw"; exit 1; }
    command -v at  >/dev/null || { echo "at fehlt (Rueckfallnetz): apt install at"; exit 1; }

    echo "Rueckfallnetz: in 10 Minuten wird der Filter automatisch abgeschaltet."
    echo "ufw disable" | at now + 10 minutes 2>&1 | tail -1
    echo "Wenn die Verbindung haelt, den geplanten Befehl entfernen:"
    echo "    atq            # Nummer ablesen"
    echo "    atrm <nummer>"
    echo

    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow "${SSH_PORT}/tcp"
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
    ufw status verbose
    ;;
  *)
    echo "Aufruf: $0 [pruefen|scharf]"; exit 1;;
esac
