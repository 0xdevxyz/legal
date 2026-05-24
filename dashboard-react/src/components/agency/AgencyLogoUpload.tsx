'use client';

import React, { useRef, useState } from 'react';
import { Image as ImageIcon, Upload, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { uploadAgencyLogo } from '@/lib/agency-api';

interface AgencyLogoUploadProps {
  onUploaded?: (relativePath: string) => void;
}

const MAX_BYTES = 2 * 1024 * 1024;

export function AgencyLogoUpload({ onUploaded }: AgencyLogoUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    setSuccess(null);
    const file = e.target.files?.[0];
    if (!file) return;
    // Client-side guard mirrors backend: PNG only, 2 MB
    if (file.type !== 'image/png') {
      setError('Nur PNG-Logos werden unterstuetzt.');
      return;
    }
    if (file.size > MAX_BYTES) {
      setError('Logo zu gross (max 2 MB).');
      return;
    }
    setPreview(URL.createObjectURL(file));
    setUploading(true);
    try {
      const res = await uploadAgencyLogo(file);
      setSuccess(`Hochgeladen: ${res.filename}`);
      onUploaded?.(res.relative_path);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? err?.message ?? 'Upload fehlgeschlagen');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
      <div className="flex items-start gap-4">
        <div className="p-3 bg-purple-500/20 rounded-lg flex-shrink-0">
          <ImageIcon className="w-5 h-5 text-purple-400" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-white font-semibold mb-1">Agentur-Logo</h3>
          <p className="text-zinc-400 text-sm mb-3">
            Wird in den generierten Client-PDFs eingebettet. PNG, max 2 MB.
          </p>

          {preview && (
            <div className="mb-3 inline-block p-2 bg-zinc-800 rounded">
              <img src={preview} alt="Logo-Vorschau" className="max-h-16" />
            </div>
          )}

          <div className="flex items-center gap-3">
            <input
              ref={inputRef}
              type="file"
              accept="image/png"
              onChange={handleSelect}
              className="hidden"
              aria-label="Logo-Datei waehlen"
            />
            <button
              onClick={() => inputRef.current?.click()}
              disabled={uploading}
              className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-60 text-white text-sm font-semibold rounded-lg transition-colors"
            >
              {uploading
                ? <Loader2 className="w-4 h-4 animate-spin" />
                : <Upload className="w-4 h-4" />}
              {uploading ? 'Wird hochgeladen ...' : 'Logo waehlen'}
            </button>
          </div>

          {success && (
            <p className="mt-2 text-green-400 text-xs flex items-center gap-1">
              <CheckCircle className="w-3 h-3" /> {success}
            </p>
          )}
          {error && (
            <p className="mt-2 text-red-400 text-xs flex items-center gap-1">
              <AlertCircle className="w-3 h-3" /> {error}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
