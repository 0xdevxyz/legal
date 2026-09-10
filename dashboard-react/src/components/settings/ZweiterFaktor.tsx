'use client';

/**
 * Zwei-Faktor-Anmeldung in den Einstellungen.
 *
 * Drei Zustände: aus, gerade in Einrichtung, an. Der mittlere ist der Grund,
 * warum das Einrichten zwei Schritte hat — wer ein Geheimnis erzeugt und die
 * Seite schliesst, ohne es in seine App zu übernehmen, wäre sonst aus dem
 * eigenen Konto ausgesperrt. Scharf wird es erst, wenn ein Code aus der App
 * angekommen ist.
 *
 * Die Wiederherstellungscodes werden GENAU EINMAL angezeigt. Das ist keine
 * Bequemlichkeitsentscheidung: gespeichert sind nur ihre bcrypt-Hashes, ein
 * zweites Anzeigen ist technisch nicht möglich. Deshalb hier ein
 * Herunterladen-Knopf und eine deutliche Warnung, bevor der Kasten weg ist.
 *
 * Kein `position: fixed` in dieser Karte: `glass-card` setzt `backdrop-filter`
 * und sperrt damit fest positionierte Kinder in die Karte ein (Befund vom
 * 06.09.2026). Alles hier fliesst im Textfluss.
 */

import React, { useCallback, useEffect, useState } from 'react';
import {
    ShieldCheck, ShieldOff, Loader2, KeyRound, Download, AlertTriangle, RefreshCw, Copy, Check,
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

type Status = { aktiv: boolean; offene_wiederherstellungscodes: number };
type Schritt = 'laedt' | 'unbekannt' | 'aus' | 'einrichten' | 'codes' | 'an';

export default function ZweiterFaktor({
    melde,
}: {
    melde: (text: string, istFehler?: boolean) => void;
}) {
    const [schritt, setSchritt] = useState<Schritt>('laedt');
    const [status, setStatus] = useState<Status | null>(null);
    const [laeuft, setLaeuft] = useState(false);

    const [geheimnis, setGeheimnis] = useState('');
    const [qrBild, setQrBild] = useState('');
    const [code, setCode] = useState('');
    const [codes, setCodes] = useState<string[]>([]);
    const [kopiert, setKopiert] = useState(false);

    const [abschaltenOffen, setAbschaltenOffen] = useState(false);
    const [abPasswort, setAbPasswort] = useState('');
    const [abCode, setAbCode] = useState('');

    const ladeStatus = useCallback(async () => {
        try {
            const daten = await apiClient.get<Status>('/api/auth/2fa/status');
            setStatus(daten);
            setSchritt(daten.aktiv ? 'an' : 'aus');
        } catch {
            // NICHT auf 'aus' fallen. Ein fehlgeschlagener Abruf sah vorher aus
            // wie "kein zweiter Faktor eingerichtet" — die Karte bot dann das
            // Einrichten an, obwohl er laeuft, und der Server wies das mit
            // "bereits aktiv" ab. Ein Fehler muss als Fehler dastehen.
            setSchritt('unbekannt');
        }
    }, []);

    useEffect(() => { ladeStatus(); }, [ladeStatus]);

    /** Die Meldung des Backends aus einem Axios-Fehler holen. */
    const fehlerAus = (e: any, rueckfall: string) => {
        const d = e?.response?.data?.detail;
        return typeof d === 'string' ? d : rueckfall;
    };

    const einrichtenStarten = async () => {
        setLaeuft(true);
        try {
            const daten = await apiClient.post<{ geheimnis: string; otpauth_uri: string }>(
                '/api/auth/2fa/einrichten');
            setGeheimnis(daten.geheimnis);
            setCode('');

            // Erst hier laden, nicht beim Seitenaufbau: die Bibliothek wird nur
            // gebraucht, wenn jemand tatsaechlich einrichtet.
            const QRCode = (await import('qrcode')).default;
            setQrBild(await QRCode.toDataURL(daten.otpauth_uri, { width: 220, margin: 1 }));

            setSchritt('einrichten');
        } catch (e: any) {
            melde(fehlerAus(e, 'Einrichtung nicht möglich.'), true);
        } finally {
            setLaeuft(false);
        }
    };

    const bestaetigen = async () => {
        setLaeuft(true);
        try {
            const daten = await apiClient.post<{ wiederherstellungscodes: string[] }>(
                '/api/auth/2fa/bestaetigen', { code });
            setCodes(daten.wiederherstellungscodes);
            setGeheimnis('');
            setQrBild('');
            setCode('');
            setSchritt('codes');
        } catch (e: any) {
            melde(fehlerAus(e, 'Der Code stimmt nicht.'), true);
        } finally {
            setLaeuft(false);
        }
    };

    const codesNeu = async () => {
        setLaeuft(true);
        try {
            const daten = await apiClient.post<{ wiederherstellungscodes: string[] }>(
                '/api/auth/2fa/codes-neu', { code });
            setCodes(daten.wiederherstellungscodes);
            setCode('');
            setSchritt('codes');
        } catch (e: any) {
            melde(fehlerAus(e, 'Der Code stimmt nicht.'), true);
        } finally {
            setLaeuft(false);
        }
    };

    const abschalten = async () => {
        setLaeuft(true);
        try {
            await apiClient.post('/api/auth/2fa/abschalten',
                { passwort: abPasswort, code: abCode });
            setAbPasswort(''); setAbCode(''); setAbschaltenOffen(false);
            melde('Zwei-Faktor-Anmeldung abgeschaltet.');
            await ladeStatus();
        } catch (e: any) {
            melde(fehlerAus(e, 'Abschalten nicht möglich.'), true);
        } finally {
            setLaeuft(false);
        }
    };

    const codesHerunterladen = () => {
        const inhalt = [
            'complyo — Wiederherstellungscodes für die Zwei-Faktor-Anmeldung',
            `Erstellt am ${new Date().toLocaleString('de-DE')}`,
            '',
            'Jeder Code lässt sich genau einmal verwenden. Bitte ausdrucken oder in',
            'einem Passwortmanager ablegen — nicht im selben Postfach wie die',
            'Anmeldemail.',
            '',
            ...codes,
            '',
        ].join('\n');
        const url = URL.createObjectURL(new Blob([inhalt], { type: 'text/plain;charset=utf-8' }));
        const a = document.createElement('a');
        a.href = url;
        a.download = 'complyo-wiederherstellungscodes.txt';
        a.click();
        URL.revokeObjectURL(url);
    };

    const codesKopieren = async () => {
        try {
            await navigator.clipboard.writeText(codes.join('\n'));
            setKopiert(true);
            setTimeout(() => setKopiert(false), 2000);
        } catch {
            melde('Kopieren hat nicht geklappt. Bitte den Download benutzen.', true);
        }
    };

    const codeFeld = (wert: string, setzen: (v: string) => void, id: string) => (
        <Input
            id={id}
            value={wert}
            onChange={(e) => setzen(e.target.value)}
            placeholder="123456"
            autoComplete="one-time-code"
            inputMode="text"
            className="tracking-[0.3em] max-w-[200px]"
        />
    );

    return (
        <Card className="glass-card border-0">
            <CardHeader>
                <CardTitle className="dark:text-white text-gray-900 flex items-center gap-2 text-base">
                    {status?.aktiv
                        ? <ShieldCheck className="w-4 h-4 text-[color:var(--lime)]" />
                        : <ShieldOff className="w-4 h-4 text-[color:var(--lime)]" />}
                    Zwei-Faktor-Anmeldung
                </CardTitle>
            </CardHeader>

            <CardContent className="space-y-4">
                {schritt === 'laedt' && (
                    <div className="flex items-center gap-2 text-sm dark:text-zinc-400 text-gray-600">
                        <Loader2 className="w-4 h-4 animate-spin" /> Status wird geladen...
                    </div>
                )}

                {schritt === 'unbekannt' && (
                    <>
                        <p className="text-sm leading-relaxed dark:text-zinc-400 text-gray-600">
                            Der Status liess sich nicht laden. Ob ein zweiter Faktor eingerichtet
                            ist, steht damit nicht fest — bitte die Seite neu laden.
                        </p>
                        <Button variant="ghost" onClick={ladeStatus} className="gap-2">
                            <RefreshCw className="w-4 h-4" /> Noch einmal versuchen
                        </Button>
                    </>
                )}

                {/* ── aus ────────────────────────────────────────────────── */}
                {schritt === 'aus' && (
                    <>
                        <p className="text-sm leading-relaxed dark:text-zinc-400 text-gray-600">
                            Ihr Konto kann Reparaturen freigeben, die auf Ihren Websites ausgeliefert
                            werden, und in verbundene Git-Depots schreiben. Ein zweiter Faktor sorgt
                            dafür, dass ein gestohlenes Passwort dafür nicht ausreicht.
                        </p>
                        <Button
                            onClick={einrichtenStarten}
                            disabled={laeuft}
                            className="bg-[var(--lime)] hover:bg-[var(--lime-bright)] text-zinc-950 gap-2"
                        >
                            {laeuft ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />}
                            Einrichten
                        </Button>
                    </>
                )}

                {/* ── einrichten ─────────────────────────────────────────── */}
                {schritt === 'einrichten' && (
                    <>
                        <p className="text-sm leading-relaxed dark:text-zinc-400 text-gray-600">
                            Scannen Sie den Code mit Ihrer Authenticator-App (etwa 1Password, Aegis
                            oder Google Authenticator) und geben Sie danach die sechs Ziffern ein,
                            die die App anzeigt. Vorher ist nichts aktiv.
                        </p>

                        {qrBild && (
                            <div className="inline-block rounded-xl bg-white p-3">
                                {/* eslint-disable-next-line @next/next/no-img-element */}
                                <img src={qrBild} alt="QR-Code zur Einrichtung der Zwei-Faktor-Anmeldung" width={220} height={220} />
                            </div>
                        )}

                        <div className="space-y-1.5">
                            <Label className="dark:text-zinc-400 text-gray-600 text-sm">
                                Falls die Kamera nicht geht: Schlüssel von Hand eintippen
                            </Label>
                            <code className="block text-xs break-all rounded-lg px-3 py-2 dark:bg-zinc-900 bg-gray-100 dark:text-zinc-300 text-gray-700">
                                {geheimnis.match(/.{1,4}/g)?.join(' ')}
                            </code>
                        </div>

                        <div className="space-y-1.5">
                            <Label htmlFor="tfa-code" className="dark:text-zinc-400 text-gray-600 text-sm">
                                Code aus der App
                            </Label>
                            {codeFeld(code, setCode, 'tfa-code')}
                        </div>

                        <div className="flex gap-2">
                            <Button
                                onClick={bestaetigen}
                                disabled={laeuft || code.length < 6}
                                className="bg-[var(--lime)] hover:bg-[var(--lime-bright)] text-zinc-950 gap-2"
                            >
                                {laeuft ? <Loader2 className="w-4 h-4 animate-spin" /> : <KeyRound className="w-4 h-4" />}
                                Aktivieren
                            </Button>
                            <Button variant="ghost" onClick={() => { setSchritt('aus'); setGeheimnis(''); setQrBild(''); }}>
                                Abbrechen
                            </Button>
                        </div>
                    </>
                )}

                {/* ── Wiederherstellungscodes ────────────────────────────── */}
                {schritt === 'codes' && (
                    <>
                        <div
                            className="p-3.5 rounded-xl flex items-start gap-3 text-sm"
                            style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.25)' }}
                        >
                            <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: '#f59e0b' }} />
                            <span className="dark:text-zinc-300 text-gray-700 leading-relaxed">
                                Diese Codes werden <strong>kein zweites Mal angezeigt</strong>. Sie sind der
                                einzige Weg zurück, wenn das Gerät mit der App verloren geht. Jeder Code
                                gilt einmal.
                            </span>
                        </div>

                        <div className="grid grid-cols-2 gap-2 font-mono text-sm rounded-xl px-3 py-3 dark:bg-zinc-900 bg-gray-100 dark:text-zinc-200 text-gray-800">
                            {codes.map((c) => <div key={c}>{c}</div>)}
                        </div>

                        <div className="flex flex-wrap gap-2">
                            <Button onClick={codesHerunterladen} className="bg-[var(--lime)] hover:bg-[var(--lime-bright)] text-zinc-950 gap-2">
                                <Download className="w-4 h-4" /> Herunterladen
                            </Button>
                            <Button variant="ghost" onClick={codesKopieren} className="gap-2">
                                {kopiert ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                                {kopiert ? 'Kopiert' : 'Kopieren'}
                            </Button>
                            <Button variant="ghost" onClick={() => { setCodes([]); ladeStatus(); }}>
                                Ich habe sie gesichert
                            </Button>
                        </div>
                    </>
                )}

                {/* ── an ─────────────────────────────────────────────────── */}
                {schritt === 'an' && (
                    <>
                        <p className="text-sm leading-relaxed dark:text-zinc-400 text-gray-600">
                            Aktiv. Bei jeder Anmeldung fragt complyo nach dem Code aus Ihrer App.
                        </p>

                        <p className="text-sm dark:text-zinc-400 text-gray-600">
                            Offene Wiederherstellungscodes:{' '}
                            <span className={
                                (status?.offene_wiederherstellungscodes ?? 0) <= 2
                                    ? 'text-amber-500 font-medium'
                                    : 'dark:text-zinc-200 text-gray-800'
                            }>
                                {status?.offene_wiederherstellungscodes ?? 0}
                            </span>
                            {(status?.offene_wiederherstellungscodes ?? 0) <= 2 && ' — Zeit für neue.'}
                        </p>

                        <div className="space-y-1.5 pt-2 border-t dark:border-zinc-800 border-gray-200">
                            <Label htmlFor="tfa-neu" className="dark:text-zinc-400 text-gray-600 text-sm">
                                Neue Wiederherstellungscodes (Code aus der App bestätigt den Wunsch)
                            </Label>
                            <div className="flex gap-2 items-center">
                                {codeFeld(code, setCode, 'tfa-neu')}
                                <Button variant="ghost" onClick={codesNeu} disabled={laeuft || code.length < 6} className="gap-2">
                                    <RefreshCw className="w-4 h-4" /> Neu erzeugen
                                </Button>
                            </div>
                            <p className="text-xs dark:text-zinc-500 text-gray-500">
                                Die bisherigen Codes verfallen dabei.
                            </p>
                        </div>

                        <div className="pt-2 border-t dark:border-zinc-800 border-gray-200">
                            {!abschaltenOffen ? (
                                <Button variant="ghost" onClick={() => setAbschaltenOffen(true)} className="gap-2 text-red-500 hover:text-red-400">
                                    <ShieldOff className="w-4 h-4" /> Zwei-Faktor-Anmeldung abschalten
                                </Button>
                            ) : (
                                <div className="space-y-3">
                                    <p className="text-sm dark:text-zinc-400 text-gray-600">
                                        Zum Abschalten brauchen wir Ihr Passwort <em>und</em> einen gültigen Code.
                                        Ein übernommener Browser hat die Sitzung, aber keins von beidem.
                                    </p>
                                    <div className="space-y-1.5">
                                        <Label htmlFor="tfa-pw" className="dark:text-zinc-400 text-gray-600 text-sm">Passwort</Label>
                                        <Input
                                            id="tfa-pw" type="password" autoComplete="current-password"
                                            value={abPasswort} onChange={(e) => setAbPasswort(e.target.value)}
                                            className="max-w-sm"
                                        />
                                    </div>
                                    <div className="space-y-1.5">
                                        <Label htmlFor="tfa-abcode" className="dark:text-zinc-400 text-gray-600 text-sm">
                                            Code aus der App oder ein Wiederherstellungscode
                                        </Label>
                                        {codeFeld(abCode, setAbCode, 'tfa-abcode')}
                                    </div>
                                    <div className="flex gap-2">
                                        <Button
                                            onClick={abschalten}
                                            disabled={laeuft || !abPasswort || !abCode}
                                            className="bg-red-600 hover:bg-red-500 text-white gap-2"
                                        >
                                            {laeuft ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldOff className="w-4 h-4" />}
                                            Abschalten
                                        </Button>
                                        <Button variant="ghost" onClick={() => { setAbschaltenOffen(false); setAbPasswort(''); setAbCode(''); }}>
                                            Abbrechen
                                        </Button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </>
                )}
            </CardContent>
        </Card>
    );
}
