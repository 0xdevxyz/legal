"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

interface ScanStatus {
  rescan_required: boolean;
  rescan_reason: string | null;
  last_scan: string | null;
  triggered_by: { id: number; title: string } | null;
}

interface Props {
  websiteId: string;
  token: string;
  onRescan?: () => void;
}

export default function RescanRequiredBanner({ websiteId, token, onRescan }: Props) {
  const [status, setStatus] = useState<ScanStatus | null>(null);
  const [dismissed, setDismissed] = useState(false);
  const router = useRouter();

  useEffect(() => {
    if (!websiteId || !token) return;

    const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";
    fetch(`${API_BASE}/api/v2/websites/${websiteId}/scan-status`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((data: ScanStatus | null) => {
        if (data?.rescan_required) setStatus(data);
      })
      .catch(() => null);
  }, [websiteId, token]);

  if (!status || dismissed) return null;

  const lastScanFormatted = status.last_scan
    ? new Date(status.last_scan).toLocaleDateString("de-DE", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
      })
    : null;

  const handleRescan = () => {
    if (onRescan) {
      onRescan();
    } else {
      router.push(`/dashboard?scan=true&website=${websiteId}`);
    }
  };

  return (
    <div className="rounded-xl border border-amber-300 bg-amber-50 dark:border-amber-700 dark:bg-amber-900/20 px-4 py-3 flex items-start gap-3">
      {/* Icon */}
      <div className="shrink-0 mt-0.5">
        <svg
          className="w-5 h-5 text-amber-600 dark:text-amber-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
          />
        </svg>
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-amber-900 dark:text-amber-200">
          Rechtliche Änderung erkannt
        </p>
        {status.triggered_by?.title && (
          <p className="text-sm text-amber-800 dark:text-amber-300 mt-0.5 truncate">
            {status.triggered_by.title}
          </p>
        )}
        {status.rescan_reason && !status.triggered_by?.title && (
          <p className="text-sm text-amber-800 dark:text-amber-300 mt-0.5">
            {status.rescan_reason}
          </p>
        )}
        {lastScanFormatted && (
          <p className="text-xs text-amber-700 dark:text-amber-400 mt-1">
            Ihr letzter Scan vom {lastScanFormatted} könnte veraltet sein.
          </p>
        )}

        {/* Actions */}
        <div className="flex items-center gap-3 mt-2">
          <button
            onClick={handleRescan}
            className="text-sm font-medium bg-amber-600 hover:bg-amber-700 text-white px-3 py-1.5 rounded-lg transition-colors"
          >
            Jetzt neu scannen
          </button>
          <button
            onClick={() => setDismissed(true)}
            className="text-xs text-amber-700 dark:text-amber-400 hover:underline"
          >
            Schließen
          </button>
        </div>
      </div>
    </div>
  );
}
