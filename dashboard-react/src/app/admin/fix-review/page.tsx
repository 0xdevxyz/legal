"use client";

import { useState, useEffect, useCallback } from "react";

interface StageLog {
  stage: number;
  name: string;
  passed: boolean;
  duration_ms: number;
  errors: string[];
  warnings: string[];
}

interface FixItem {
  id: number;
  fix_type: string;
  issue_title: string;
  quality_gate_status: string;
  quality_gate_log: StageLog[] | null;
  applied_at: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  website_url: string | null;
  user_email: string | null;
}

interface ReviewQueue {
  items: FixItem[];
  total: number;
  limit: number;
  offset: number;
}

const ADMIN_KEY = process.env.NEXT_PUBLIC_ADMIN_API_KEY ?? "";
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

export default function FixReviewPage() {
  const [queue, setQueue] = useState<ReviewQueue | null>(null);
  const [selected, setSelected] = useState<FixItem | null>(null);
  const [rejectReason, setRejectReason] = useState("");
  const [loading, setLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState<{ type: "ok" | "err"; text: string } | null>(null);

  const fetchQueue = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(
        `${API_BASE}/api/admin/fix-review-queue?api_key=${ADMIN_KEY}&limit=50&offset=0`
      );
      if (!res.ok) throw new Error(await res.text());
      setQueue(await res.json());
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setActionMsg({ type: "err", text: `Laden fehlgeschlagen: ${msg}` });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchQueue();
  }, [fetchQueue]);

  const doAction = async (fixId: number, action: "approve" | "reject") => {
    setLoading(true);
    setActionMsg(null);
    try {
      const body =
        action === "reject"
          ? JSON.stringify({ reason: rejectReason })
          : undefined;
      const res = await fetch(
        `${API_BASE}/api/admin/fix-review-queue/${fixId}/${action}?api_key=${ADMIN_KEY}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body,
        }
      );
      if (!res.ok) throw new Error(await res.text());
      setActionMsg({
        type: "ok",
        text: action === "approve" ? "Fix freigegeben." : "Fix abgelehnt.",
      });
      setSelected(null);
      setRejectReason("");
      await fetchQueue();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setActionMsg({ type: "err", text: msg });
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
            Fix Review Queue
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            KI-generierte Fixes, die das automatische Quality Gate nicht bestanden haben
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
                Ausstehend ({queue?.total ?? 0})
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

            {queue?.items.length === 0 && (
              <div className="p-8 text-center dark:text-gray-400 text-gray-600 text-sm">
                Keine offenen Reviews
              </div>
            )}

            <ul className="divide-y divide-gray-100 dark:divide-gray-800">
              {queue?.items.map((item) => (
                <li
                  key={item.id}
                  onClick={() => setSelected(item)}
                  className={`px-4 py-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors ${
                    selected?.id === item.id
                      ? "bg-blue-50 dark:bg-blue-900/20 border-l-2 border-blue-500"
                      : ""
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                        {item.issue_title ?? `Fix #${item.id}`}
                      </p>
                      <p className="text-xs text-gray-500 truncate mt-0.5">
                        {item.website_url ?? item.user_email ?? "—"}
                      </p>
                    </div>
                    <span
                      className={`shrink-0 text-xs px-2 py-0.5 rounded-full font-medium ${
                        item.fix_type === "code"
                          ? "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300"
                          : item.fix_type === "text"
                          ? "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300"
                          : "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400"
                      }`}
                    >
                      {item.fix_type}
                    </span>
                  </div>
                  <p className="text-xs dark:text-gray-400 text-gray-600 mt-1">
                    {new Date(item.applied_at).toLocaleString("de-DE")}
                  </p>
                  <FailedStages log={item.quality_gate_log} />
                </li>
              ))}
            </ul>
          </div>

          {/* Detail panel */}
          <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800">
            {!selected ? (
              <div className="p-10 text-center dark:text-gray-400 text-gray-600 text-sm">
                Fix aus der Liste wählen
              </div>
            ) : (
              <div className="p-5 space-y-5">
                <div>
                  <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100">
                    {selected.issue_title ?? `Fix #${selected.id}`}
                  </h2>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {selected.website_url} · {selected.user_email}
                  </p>
                </div>

                {/* Quality Gate Log */}
                <div>
                  <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-2">
                    Quality Gate Log
                  </h3>
                  <div className="space-y-2">
                    {(selected.quality_gate_log ?? []).map((s) => (
                      <div
                        key={s.stage}
                        className={`rounded-lg px-3 py-2 text-sm border ${
                          s.passed
                            ? "border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20"
                            : "border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20"
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <span className={s.passed ? "text-green-600" : "text-red-600"}>
                            {s.passed ? "✓" : "✗"}
                          </span>
                          <span className="font-medium text-gray-800 dark:text-gray-200">
                            Stufe {s.stage}: {s.name}
                          </span>
                          <span className="ml-auto text-xs dark:text-gray-400 text-gray-600">
                            {s.duration_ms}ms
                          </span>
                        </div>
                        {s.errors.map((e, i) => (
                          <p key={i} className="text-xs text-red-700 dark:text-red-400 mt-1 ml-5">
                            {e}
                          </p>
                        ))}
                        {s.warnings.map((w, i) => (
                          <p key={i} className="text-xs text-yellow-700 dark:text-yellow-400 mt-1 ml-5">
                            ⚠ {w}
                          </p>
                        ))}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Actions */}
                <div className="space-y-3 pt-2 border-t border-gray-100 dark:border-gray-800">
                  <button
                    onClick={() => doAction(selected.id, "approve")}
                    disabled={loading}
                    className="w-full py-2.5 rounded-lg bg-green-600 hover:bg-green-700 dark:text-white text-gray-900 text-sm font-medium transition-colors disabled:opacity-50"
                  >
                    Fix freigeben
                  </button>

                  <div className="space-y-2">
                    <textarea
                      value={rejectReason}
                      onChange={(e) => setRejectReason(e.target.value)}
                      placeholder="Begründung für Ablehnung (min. 5 Zeichen)…"
                      rows={2}
                      className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-red-400"
                    />
                    <button
                      onClick={() => doAction(selected.id, "reject")}
                      disabled={loading || rejectReason.trim().length < 5}
                      className="w-full py-2.5 rounded-lg bg-red-600 hover:bg-red-700 dark:text-white text-gray-900 text-sm font-medium transition-colors disabled:opacity-50"
                    >
                      Fix ablehnen
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function FailedStages({ log }: { log: StageLog[] | null }) {
  if (!log) return null;
  const failed = log.filter((s) => !s.passed);
  if (failed.length === 0) return null;
  return (
    <div className="flex gap-1 mt-1 flex-wrap">
      {failed.map((s) => (
        <span
          key={s.stage}
          className="text-xs bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300 px-1.5 py-0.5 rounded"
        >
          Stufe {s.stage} fehlgeschlagen
        </span>
      ))}
    </div>
  );
}
