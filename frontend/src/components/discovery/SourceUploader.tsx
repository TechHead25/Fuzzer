"use client";

import { useState, useCallback } from 'react';
import { Upload, FileArchive, CheckCircle, AlertCircle, Loader2, X } from 'lucide-react';
import { clsx } from 'clsx';
import axios from 'axios';
import { DiscoveryJobStatus } from '@/types/discovery';
import { ProgressBar } from './ui';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

interface Props {
  projectId: number;
  onComplete: () => void;
}

export function SourceUploader({ projectId, onComplete }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [minScore, setMinScore] = useState(1.0);
  const [dragging, setDragging] = useState(false);
  const [job, setJob] = useState<DiscoveryJobStatus | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped?.name.endsWith('.zip')) setFile(dropped);
    else setError('Only .zip archives are accepted');
  }, []);

  const poll = useCallback(async (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const res = await axios.get<DiscoveryJobStatus>(
          `${API}/api/v1/projects/${projectId}/targets/discover/status/${jobId}`
        );
        setJob(res.data);
        if (res.data.status === 'complete' || res.data.status === 'error') {
          clearInterval(interval);
          if (res.data.status === 'complete') onComplete();
        }
      } catch {
        clearInterval(interval);
      }
    }, 1500);
  }, [projectId, onComplete]);

  const handleSubmit = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    const form = new FormData();
    form.append('source_zip', file);
    form.append('min_score', String(minScore));
    try {
      const res = await axios.post<DiscoveryJobStatus>(
        `${API}/api/v1/projects/${projectId}/targets/discover/source`,
        form,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      setJob(res.data);
      poll(res.data.job_id);
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

  return (
    <div className="space-y-5">
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
        onClick={() => document.getElementById('zip-input')?.click()}
      >
        <input
          id="zip-input"
          type="file"
          accept=".zip"
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
              <p className="text-sm font-medium text-zinc-400">Drop a .zip of C/C++ source files</p>
              <p className="text-xs mt-1">or click to browse — max 100 MB</p>
            </div>
          </div>
        )}
      </div>

      {/* Min score */}
      <div className="flex items-center gap-4">
        <label className="text-sm text-zinc-400 whitespace-nowrap">Min risk score</label>
        <input
          type="range"
          min={0} max={5} step={0.5}
          value={minScore}
          onChange={e => setMinScore(Number(e.target.value))}
          className="flex-1 accent-blue-500"
        />
        <span className="text-sm font-mono text-zinc-300 w-8 text-right">{minScore}</span>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-start gap-2 text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Job progress */}
      {job && (
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-zinc-400">{job.message}</span>
            <span className="text-zinc-500 font-mono">{Math.round(job.progress * 100)}%</span>
          </div>
          <ProgressBar value={job.progress} />
          {job.status === 'complete' && job.result && (
            <div className="flex items-center gap-2 text-emerald-400 text-sm">
              <CheckCircle className="w-4 h-4" />
              <span>
                {job.result.saved_to_db} targets saved
                ({job.result.above_threshold} above threshold of {job.result.min_score})
              </span>
            </div>
          )}
          {job.status === 'error' && (
            <div className="flex items-start gap-2 text-red-400 text-sm">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{job.error}</span>
            </div>
          )}
        </div>
      )}

      <button
        onClick={handleSubmit}
        disabled={!file || uploading || (job?.status === 'running' || job?.status === 'pending')}
        className="w-full py-2.5 px-4 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium transition-colors flex items-center justify-center gap-2"
      >
        {uploading || job?.status === 'running' || job?.status === 'pending'
          ? <><Loader2 className="w-4 h-4 animate-spin" /> Analyzing…</>
          : <><Upload className="w-4 h-4" /> Start Analysis</>}
      </button>
    </div>
  );
}
