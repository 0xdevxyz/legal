"use client";

import { useState, useEffect, useCallback } from "react";
import { getApiClient } from "@/lib/api-client";

// Deklarative Compliance-Checks, die der Legal-Change-Monitor automatisch
// erzeugt hat und die auf das Admin-GO warten (status = 'pending_review').
// API: legal_change_routes.py — /api/legal-changes/checks/*
interface CheckItem {
  id: number;
  slug: string;
  category: string | null;
  title: string;
  description: string | null;
  recommendation: string | null;
  legal_basis: string | null;
  severity: string | null;
  risk_euro: number | null;
  applies_when: Record<string, unknown> | null;
  detection: Record<string, unknown> | null;
  effective_date: string | null;
  status: string;
  auto_generated: boolean;
  source_legal_update_id: number | null;
  generation_notes: string | null;
  created_at: string;
}

interface PendingResponse {
  pending: CheckItem[];
  count: number;
}

// Zugang laeuft wie bei fix-review ueber die normale Anmeldung (JWT) und die
// Rolle "admin" (require_admin im Backend).
const api = getApiClient();

/** Fehlertext aus einer Axios-Antwort, mit verstaendlicher Meldung bei 401/403. */
function fehlertext(e: unknown): string {
  const err = e as { response?: { status?: number; data?: { detail?: string } }; message?: string };
  const status = err?.response?.status;
  if (status === 401) return "Nicht angemeldet.";
  if (status === 403) return "Dieser Bereich ist Konten mit der Rolle \"admin\" vorbehalten.";
  return err?.response?.data?.detail || err?.message || "Unbekannter Fehler";
}

const SEVERITY_BADGE: Record<string, string> = {
  critical: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300",
  high: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300",
  medium: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300",
  low: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300",
};

function SeverityBadge({ severity }: { severity: string | null }) {
  const cls =
    (severity && SEVERITY_BADGE[severity]) ||
    "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400";
  return (
    <span className={`shrink-0 text-xs px-2 py-0.5 rounded-full font-medium ${cls}`}>
      {severity ?? "—"}
    </span>
  );
}

/** JSON-Detailblock (applies_when / detection) — scrollt in sich selbst. */
function JsonBlock({ label, value }: { label: string; value: unknown }) {
  if (value == null) return null;
  return (
    <div>
      <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-2">
        {label}
      </h3>
      <pre className="text-xs rounded-lg border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/60 text-gray-800 dark:text-gray-200 p-3 overflow-x-auto whitespace-pre-wrap break-words">
        {JSON.stringify(value, null, 2)}
      </pre>
    </div>
  );
}

function TextRow({ label, value }: { label: string; value: string | null }) {
  if (!value) return null;
  return (
    <div>
      <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1">
        {label}
      </h3>
      <p className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap">{value}</p>
    </div>
  );
}

export default function CheckReviewPage() {
  const [queue, setQueue] = useState<PendingResponse | null>(null);
  const [selected, setSelected] = useState<CheckItem | null>(null);
  const [loading, setLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState<{ type: "ok" | "err"; text: string } | null>(null);
  // Ablehnungs-Begruendung: wird beim Verwerfen an die Admin-API geschickt
  // (POST /checks/{id}/dismiss, Body {reason}) und dort in generation_notes
  // persistiert.
  const [dismissReason, setDismissReason] = useState("");

  const fetchQueue = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get<PendingResponse>("/api/legal-changes/checks/pending");
      setQueue(res.data);
    } catch (e: unknown) {
      setActionMsg({ type: "err", text: `Laden fehlgeschlagen: ${fehlertext(e)}` });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchQueue();
  }, [fetchQueue]);

  const doAction = async (checkId: number, action: "activate" | "dismiss") => {
    if (action === "dismiss") {
      const ok = window.confirm(
        "Diesen Check wirklich verwerfen? Er wird auf 'disabled' gesetzt und laeuft in keinem Scan."
      );
      if (!ok) return;
    }
    setLoading(true);
    setActionMsg(null);
    try {
      // /dismiss nimmt eine optionale Begruendung entgegen und haengt sie
      // backendseitig an generation_notes an.
      const body =
        action === "dismiss" && dismissReason.trim()
          ? { reason: dismissReason.trim() }
          : undefined;
      await api.post(`/api/legal-changes/checks/${checkId}/${action}`, body);
      setActionMsg({
        type: "ok",
        text:
          action === "activate"
            ? "Check freigegeben — ab dem naechsten Scan aktiv."
            : "Check verworfen (disabled).",
      });
      setSelected(null);
      setDismissReason("");
      await fetchQueue();
    } catch (e: unknown) {
      setActionMsg({ type: "err", text: fehlertext(e) });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="px-4 sm:px-6 py-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Check Review Queue
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Automatisch generierte Compliance-Checks, die auf das Admin-GO warten
          </p>
        </div>

        {actionMsg && (
          <div
            className={`mb-4 px-4 py-3 rounded-lg text-sm font-medium ${
              actionMsg.type === "ok"
                ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300"
                : "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300"
            }`}
          >
            {actionMsg.text}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Queue list */}
          <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between">
              <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                Ausstehend ({queue?.count ?? 0})
              </span>
              <button
                onClick={fetchQueue}
                disabled={loading}
                className="text-xs text-blue-600 hover:underline disabled:opacity-50"
              >
                Aktualisieren
              </button>
            </div>

            {loading && !queue && (
              <div className="p-8 text-center dark:text-gray-400 text-gray-600 text-sm">Laden…</div>
            )}

            {queue?.pending.length === 0 && (
              <div className="p-8 text-center dark:text-gray-400 text-gray-600 text-sm">
                Keine offenen Reviews
              </div>
            )}

            <ul className="divide-y divide-gray-100 dark:divide-gray-800">
              {queue?.pending.map((item) => (
                <li
                  key={item.id}
                  onClick={() => {
                    setSelected(item);
                    setDismissReason("");
                  }}
                  className={`px-4 py-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors ${
                    selected?.id === item.id
                      ? "bg-blue-50 dark:bg-blue-900/20 border-l-2 border-blue-500"
                      : ""
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                        {item.title ?? item.slug}
                      </p>
                      <p className="text-xs text-gray-500 truncate mt-0.5">
                        {item.slug}
                        {item.category ? ` · ${item.category}` : ""}
                      </p>
                    </div>
                    <SeverityBadge severity={item.severity} />
                  </div>
                  <p className="text-xs dark:text-gray-400 text-gray-600 mt-1">
                    {new Date(item.created_at).toLocaleString("de-DE")}
                    {item.legal_basis ? ` · ${item.legal_basis}` : ""}
                  </p>
                </li>
              ))}
            </ul>
          </div>

          {/* Detail panel */}
          <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800">
            {!selected ? (
              <div className="p-10 text-center dark:text-gray-400 text-gray-600 text-sm">
                Check aus der Liste wählen
              </div>
            ) : (
              <div className="p-5 space-y-5">
                <div>
                  <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100">
                    {selected.title ?? selected.slug}
                  </h2>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {selected.slug}
                    {selected.category ? ` · ${selected.category}` : ""}
                    {selected.risk_euro != null ? ` · Risiko bis ${selected.risk_euro} €` : ""}
                    {selected.effective_date
                      ? ` · wirksam ab ${new Date(selected.effective_date).toLocaleDateString("de-DE")}`
                      : ""}
                  </p>
                </div>

                <TextRow label="Beschreibung" value={selected.description} />
                <TextRow label="Empfehlung" value={selected.recommendation} />
                <TextRow label="Rechtsgrundlage" value={selected.legal_basis} />

                {/* Herkunft der Generierung */}
                {(selected.generation_notes || selected.source_legal_update_id != null) && (
                  <div>
                    <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1">
                      Generierung
                    </h3>
                    {selected.source_legal_update_id != null && (
                      <p className="text-xs dark:text-gray-400 text-gray-600">
                        Quelle: Legal-Update #{selected.source_legal_update_id}
                      </p>
                    )}
                    {selected.generation_notes && (
                      <p className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap mt-1">
                        {selected.generation_notes}
                      </p>
                    )}
                  </div>
                )}

                {/* Generierter Check-Inhalt */}
                <JsonBlock label="Gilt wenn (applies_when)" value={selected.applies_when} />
                <JsonBlock label="Erkennung (detection)" value={selected.detection} />

                {/* Actions */}
                <div className="space-y-3 pt-2 border-t border-gray-100 dark:border-gray-800">
                  <button
                    onClick={() => doAction(selected.id, "activate")}
                    disabled={loading}
                    className="w-full py-2.5 rounded-lg bg-green-600 hover:bg-green-700 dark:text-white text-gray-900 text-sm font-medium transition-colors disabled:opacity-50"
                  >
                    Check freigeben (aktiv schalten)
                  </button>

                  <div>
                    <label
                      htmlFor="dismiss-reason"
                      className="block text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1"
                    >
                      Begründung fürs Verwerfen (optional)
                    </label>
                    <textarea
                      id="dismiss-reason"
                      value={dismissReason}
                      onChange={(e) => setDismissReason(e.target.value)}
                      rows={2}
                      placeholder="z.B. Prüfung fachlich falsch, Rechtsgrundlage passt nicht …"
                      className="w-full text-sm rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-800/60 text-gray-800 dark:text-gray-200 p-2.5 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-red-500/40"
                    />
                  </div>

                  <button
                    onClick={() => doAction(selected.id, "dismiss")}
                    disabled={loading}
                    className="w-full py-2.5 rounded-lg bg-red-600 hover:bg-red-700 dark:text-white text-gray-900 text-sm font-medium transition-colors disabled:opacity-50"
                  >
                    Check verwerfen
                  </button>
                  <p className="text-xs text-gray-500">
                    Verwerfen setzt den Check auf &quot;disabled&quot;. Die Begründung wird in den
                    Generierungs-Notizen des Checks gespeichert.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
