"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ExternalLink, RefreshCw, BookOpen, AlertTriangle } from "lucide-react";

interface KnowledgeUpdate {
  id: string;
  title: string;
  date: string;
  law_areas: string[];
  impact: "high" | "medium" | "low";
  relevance_score: number;
  source_type: string;
  tags: string[];
  obsidian_deep_link: string;
  source_url: string;
}

interface KnowledgeFeedProps {
  maxItems?: number;
  showFilter?: boolean;
}

const IMPACT_CONFIG = {
  high: { label: "Hoch", className: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300" },
  medium: { label: "Mittel", className: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300" },
  low: { label: "Niedrig", className: "bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300" },
};

const SOURCE_LABELS: Record<string, string> = {
  eulex: "EUR-Lex",
  bfdi: "BfDI",
  web: "Web",
  internal: "intern",
};

async function fetchKnowledgeUpdates(impact?: string): Promise<KnowledgeUpdate[]> {
  const params = new URLSearchParams({ limit: "10" });
  if (impact) params.set("impact", impact);
  const res = await fetch(`/api/knowledge/updates?${params.toString()}`);
  if (!res.ok) return [];
  const data = await res.json();
  return data.updates ?? [];
}

export function KnowledgeFeed({ maxItems = 5, showFilter = true }: KnowledgeFeedProps) {
  const [updates, setUpdates] = useState<KnowledgeUpdate[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterImpact, setFilterImpact] = useState<string>("");
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadUpdates();
  }, [filterImpact]);

  async function loadUpdates() {
    setLoading(true);
    try {
      const data = await fetchKnowledgeUpdates(filterImpact || undefined);
      setUpdates(data.slice(0, maxItems));
    } catch (e) {
      console.error("KnowledgeFeed load error:", e);
    } finally {
      setLoading(false);
    }
  }

  async function handleRefresh() {
    setRefreshing(true);
    try {
      await fetch("/api/knowledge/trigger-refresh", { method: "POST" });
      await new Promise((r) => setTimeout(r, 2000));
      await loadUpdates();
    } finally {
      setRefreshing(false);
    }
  }

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <div className="flex items-center gap-2">
          <BookOpen className="h-5 w-5 text-blue-600 dark:text-blue-400" />
          <CardTitle className="text-base font-semibold">Compliance-Wissen</CardTitle>
        </div>
        <div className="flex items-center gap-2">
          {showFilter && (
            <div className="flex gap-1">
              {["", "high", "medium", "low"].map((imp) => (
                <button
                  key={imp}
                  onClick={() => setFilterImpact(imp)}
                  className={`rounded-md px-2 py-1 text-xs transition-colors ${
                    filterImpact === imp
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300"
                  }`}
                >
                  {imp === "" ? "Alle" : IMPACT_CONFIG[imp as keyof typeof IMPACT_CONFIG]?.label}
                </button>
              ))}
            </div>
          )}
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="rounded-md p-1.5 text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-gray-700 disabled:opacity-50"
            title="Wissen aktualisieren"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
          </button>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        {loading ? (
          <div className="space-y-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-16 animate-pulse rounded-lg bg-gray-100 dark:bg-gray-700" />
            ))}
          </div>
        ) : updates.length === 0 ? (
          <div className="flex flex-col items-center gap-2 py-6 text-center text-sm text-gray-500">
            <BookOpen className="h-8 w-8 opacity-40" />
            <p>Noch keine Wissens-Updates vorhanden.</p>
            <p className="text-xs">Der Cronjob läuft täglich um 07:00 Uhr.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {updates.map((update) => (
              <KnowledgeUpdateItem key={update.id} update={update} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function KnowledgeUpdateItem({ update }: { update: KnowledgeUpdate }) {
  const impact = IMPACT_CONFIG[update.impact] ?? IMPACT_CONFIG.low;

  return (
    <div className="group rounded-lg border border-gray-100 bg-gray-50 p-3 transition-colors hover:border-blue-200 hover:bg-blue-50/30 dark:border-gray-700 dark:bg-gray-800/50 dark:hover:border-blue-700">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-gray-900 dark:text-gray-100">
            {update.title}
          </p>
          <div className="mt-1 flex flex-wrap items-center gap-1.5">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {update.date} · {SOURCE_LABELS[update.source_type] ?? update.source_type}
            </span>
            {update.law_areas.slice(0, 3).map((area) => (
              <span
                key={area}
                className="rounded-full bg-blue-100 px-1.5 py-0.5 text-xs text-blue-700 dark:bg-blue-900/30 dark:text-blue-300"
              >
                {area}
              </span>
            ))}
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-1.5">
          {update.impact === "high" && (
            <AlertTriangle className="h-3.5 w-3.5 text-red-500" />
          )}
          <Badge className={`text-xs ${impact.className}`}>{impact.label}</Badge>
          <div className="flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
            {update.obsidian_deep_link && (
              <a
                href={update.obsidian_deep_link}
                title="In Obsidian öffnen"
                className="rounded p-1 text-gray-400 hover:text-purple-600"
              >
                <BookOpen className="h-3.5 w-3.5" />
              </a>
            )}
            {update.source_url && (
              <a
                href={update.source_url}
                target="_blank"
                rel="noopener noreferrer"
                title="Quelle öffnen"
                className="rounded p-1 text-gray-400 hover:text-blue-600"
              >
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
