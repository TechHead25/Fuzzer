"use client";

import { useState, useCallback, useEffect } from 'react';
import { Upload, FileArchive, CheckCircle, AlertCircle, Loader2, X, Info } from 'lucide-react';
import { clsx } from 'clsx';
import axios from 'axios';
import { ImportFormatDoc, ImportSessionSummary } from '@/types/workspace';
import { ProgressBar } from '@/components/discovery/ui';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

interface Props {
  projectId: number;
  onComplete: () => void;
}

export function WorkspaceUploader({ projectId, onComplete }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [importType, setImportType] = useState('re_notes');
  const [formats, setFormats] = useState<ImportFormatDoc[]>([]);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [session, setSession] = useState<ImportSessionSummary | null>(null);

  useEffect(() => {
    axios.get<ImportFormatDoc[]>(`${API}/api/v1/projects/${projectId}/workspace/import-formats`)
      .then(res => setFormats(res.data))
      .catch(err => console.error(err));
  }, [projectId]);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) setFile(dropped);
  }, []);

  const handleSubmit = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    const form = new FormData();
    form.append('evidence_file', file);
    form.append('import_type', importType);
    try {
      const res = await axios.post<ImportSessionSummary>(
        `${API}/api/v1/projects/${projectId}/workspace/import`,
        form,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      setSession(res.data);
      onComplete();
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail ?? err.message);
      } else {
        setError('Upload failed');
      }
    } finally {
      setUploading(false);
    }
  };

  const selectedFormat = formats.find(f => f.import_type === importType);

  return (
    <div className="space-y-5">
      {/* Format selector */}
      <div>
        <label className="text-sm font-medium text-zinc-300 block mb-2">Import Format</label>
        <select
          value={importType}
          onChange={e => setImportType(e.target.value)}
          className="w-full bg-zinc-900 border border-zinc-700 text-zinc-300 text-sm rounded-lg px-4 py-2.5 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
        >
          {formats.map(f => (
            <option key={f.import_type} value={f.import_type}>{f.display_name}</option>
          ))}
        </select>
        
        {selectedFormat && (
          <div className="mt-3 bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-3 text-sm">
            <p className="text-zinc-400">{selectedFormat.description}</p>
            {selectedFormat.notes && (
              <div className="flex items-start gap-2 mt-2 text-blue-400/90 text-xs">
                <Info className="w-4 h-4 shrink-0 mt-0.5" />
                <p>{selectedFormat.notes}</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Drop zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={clsx(
          'border-2 border-dashed rounded-lg p-10 text-center transition-colors cursor-pointer',
          dragging ? 'border-blue-500 bg-blue-500/5' : 'border-zinc-700 hover:border-zinc-600',
          file && 'border-emerald-600/50 bg-emerald-500/5'
        )}
        onClick={() => document.getElementById('evidence-input')?.click()}
      >
        <input
          id="evidence-input"
          type="file"
          accept={selectedFormat?.accepted_extensions.join(',')}
          className="hidden"
          onChange={e => { if (e.target.files?.[0]) setFile(e.target.files[0]); }}
        />
        {file ? (
          <div className="flex flex-col items-center gap-2">
            <FileArchive className="w-8 h-8 text-emerald-500" />
            <span className="text-sm font-medium text-zinc-300">{file.name}</span>
            <span className="text-xs text-zinc-500">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
            <button
              className="text-xs text-zinc-500 hover:text-zinc-300 flex items-center gap-1 mt-1"
              onClick={e => { e.stopPropagation(); setFile(null); }}
            >
              <X className="w-3 h-3" /> Remove
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3 text-zinc-500">
            <Upload className="w-8 h-8" />
            <div>
              <p className="text-sm font-medium text-zinc-400">Drop your evidence file</p>
              <p className="text-xs mt-1">Accepts {selectedFormat?.accepted_extensions.join(', ')}</p>
            </div>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-start gap-2 text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Success state */}
      {session && session.status === 'complete' && (
        <div className="flex items-center gap-2 text-emerald-400 text-sm bg-emerald-500/10 border border-emerald-500/20 rounded-lg px-4 py-3">
          <CheckCircle className="w-4 h-4 shrink-0" />
          <span>Imported {session.targets_imported} targets successfully!</span>
        </div>
      )}

      <button
        onClick={handleSubmit}
        disabled={!file || uploading}
        className="w-full py-2.5 px-4 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium transition-colors flex items-center justify-center gap-2"
      >
        {uploading
          ? <><Loader2 className="w-4 h-4 animate-spin" /> Uploading…</>
          : <><Upload className="w-4 h-4" /> Import Evidence</>}
      </button>
    </div>
  );
}
