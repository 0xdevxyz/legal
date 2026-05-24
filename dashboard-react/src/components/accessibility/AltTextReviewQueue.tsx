'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { CheckCircle, XCircle, Clock, Image as ImageIcon, RefreshCw } from 'lucide-react';
import { apiClient } from '@/lib/api';

interface AltTextReviewItem {
  id: number;
  site_id: string;
  image_src: string;
  suggested_alt: string;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
  reviewed_at?: string;
  approved_alt?: string;
}

interface QueueResponse {
  items: AltTextReviewItem[];
  total: number;
  pending: number;
}

export default function AltTextReviewQueue() {
  const [data, setData] = useState<QueueResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editValue, setEditValue] = useState('');
  const [actionLoading, setActionLoading] = useState<number | null>(null);

  const loadQueue = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiClient.get<QueueResponse>('/api/v2/accessibility/alt-text-review');
      setData(res.data);
    } catch {
      setData({ items: [], total: 0, pending: 0 });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadQueue();
  }, [loadQueue]);

  const handleApprove = async (item: AltTextReviewItem) => {
    const altToApprove = editingId === item.id ? editValue : item.suggested_alt;
    setActionLoading(item.id);
    try {
      await apiClient.post(`/api/v2/accessibility/alt-text-review/${item.id}/approve`, {
        approved_alt: altToApprove,
      });      setEditingId(null);
      await loadQueue();
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (itemId: number) => {
    setActionLoading(itemId);
    try {
      await apiClient.post(`/api/v2/accessibility/alt-text-review/${itemId}/reject`, {});
      await loadQueue();
    } finally {
      setActionLoading(null);
    }
  };

  const statusIcon = (status: string) => {
    if (status === 'approved') return <CheckCircle className="w-4 h-4 text-green-400" />;
    if (status === 'rejected') return <XCircle className="w-4 h-4 text-red-400" />;
    return <Clock className="w-4 h-4 text-amber-400" />;
  };

  const statusLabel = (status: string) => {
    if (status === 'approved') return 'Freigegeben';
    if (status === 'rejected') return 'Abgelehnt';
    return 'Ausstehend';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <RefreshCw className="w-6 h-6 text-blue-400 animate-spin mr-2" />
        <span className="text-gray-400">Lade Review-Queue...</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Alt-Text Review Queue</h2>
          <p className="text-sm text-gray-400 mt-0.5">
            KI-generierte Alt-Texte müssen manuell freigegeben werden bevor sie deployed werden.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {data && data.pending > 0 && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-amber-500/15 border border-amber-500/30 rounded-full text-amber-300 text-sm font-medium">
              <Clock className="w-3.5 h-3.5" />
              {data.pending} ausstehend
            </span>
          )}
          <button
            onClick={loadQueue}
            className="p-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-gray-400 hover:text-white transition-colors"
            aria-label="Queue neu laden"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {!data || data.items.length === 0 ? (
        <div className="text-center py-16 bg-zinc-900/50 border border-zinc-800 rounded-xl">
          <CheckCircle className="w-10 h-10 text-green-400 mx-auto mb-3" />
          <p className="text-gray-300 font-medium">Keine Alt-Texte in der Queue</p>
          <p className="text-gray-500 text-sm mt-1">Alle KI-Vorschläge wurden bereits bearbeitet.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {data.items.map((item) => (
            <div
              key={item.id}
              className={`bg-zinc-900/60 border rounded-xl p-4 transition-all ${
                item.status === 'pending'
                  ? 'border-amber-500/30'
                  : item.status === 'approved'
                  ? 'border-green-500/20'
                  : 'border-red-500/20 opacity-60'
              }`}
            >
              <div className="flex items-start gap-4">
                <div className="w-16 h-16 flex-shrink-0 rounded-lg bg-zinc-800 border border-zinc-700 flex items-center justify-center overflow-hidden">
                  {item.image_src.startsWith('http') ? (
                    <img
                      src={item.image_src}
                      alt=""
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                  ) : (
                    <ImageIcon className="w-6 h-6 text-gray-600" />
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    {statusIcon(item.status)}
                    <span className="text-xs text-gray-400">{statusLabel(item.status)}</span>
                    <span className="text-xs text-gray-600 ml-auto">
                      {item.site_id} · {new Date(item.created_at).toLocaleDateString('de-DE')}
                    </span>
                  </div>

                  <p className="text-xs text-gray-500 truncate mb-2">{item.image_src}</p>

                  {item.status === 'pending' && editingId === item.id ? (
                    <textarea
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      className="w-full bg-zinc-800 border border-blue-500/50 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                      rows={2}
                      aria-label="Alt-Text bearbeiten"
                    />
                  ) : (
                    <p className="text-sm text-gray-200 bg-zinc-800/50 rounded-lg px-3 py-2">
                      {item.approved_alt || item.suggested_alt}
                    </p>
                  )}
                </div>
              </div>

              {item.status === 'pending' && (
                <div className="flex items-center justify-end gap-2 mt-3">
                  {editingId === item.id ? (
                    <>
                      <button
                        onClick={() => setEditingId(null)}
                        className="px-3 py-1.5 text-xs text-gray-400 hover:text-white bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
                      >
                        Abbrechen
                      </button>
                      <button
                        onClick={() => handleApprove(item)}
                        disabled={actionLoading === item.id || !editValue.trim()}
                        className="px-3 py-1.5 text-xs text-white bg-green-600 hover:bg-green-500 disabled:opacity-40 rounded-lg transition-colors flex items-center gap-1"
                      >
                        <CheckCircle className="w-3.5 h-3.5" />
                        Freigeben
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        onClick={() => handleReject(item.id)}
                        disabled={actionLoading === item.id}
                        className="px-3 py-1.5 text-xs text-red-400 hover:text-red-300 bg-zinc-800 hover:bg-zinc-700 disabled:opacity-40 rounded-lg transition-colors flex items-center gap-1"
                      >
                        <XCircle className="w-3.5 h-3.5" />
                        Ablehnen
                      </button>
                      <button
                        onClick={() => {
                          setEditingId(item.id);
                          setEditValue(item.suggested_alt);
                        }}
                        className="px-3 py-1.5 text-xs text-blue-400 hover:text-blue-300 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
                      >
                        Bearbeiten
                      </button>
                      <button
                        onClick={() => handleApprove(item)}
                        disabled={actionLoading === item.id}
                        className="px-3 py-1.5 text-xs text-white bg-green-600 hover:bg-green-500 disabled:opacity-40 rounded-lg transition-colors flex items-center gap-1"
                      >
                        <CheckCircle className="w-3.5 h-3.5" />
                        Freigeben
                      </button>
                    </>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
