"use client";

import { useState } from 'react';
import { X, ShieldCheck, Loader2 } from 'lucide-react';
import axios from 'axios';
import { TargetDetail } from '@/types/discovery';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

interface Props {
  projectId: number;
  target: TargetDetail;
  onClose: () => void;
  onComplete: () => void;
}

const TRANSITIONS: Record<string, string[]> = {
  DISCOVERED:      ['REVIEW_REQUIRED', 'DISABLED'],
  REVIEW_REQUIRED: ['VERIFIED', 'DISCOVERED', 'DISABLED'],
  VERIFIED:        ['HARNESS_READY', 'REVIEW_REQUIRED', 'DISABLED'],
  HARNESS_READY:   ['FUZZING_READY', 'VERIFIED', 'DISABLED'],
  FUZZING_READY:   ['ACTIVE', 'HARNESS_READY', 'DISABLED'],
  ACTIVE:          ['FUZZING_READY', 'DISABLED'],
  DISABLED:        ['DISCOVERED'],
};

export function VerificationModal({ projectId, target, onClose, onComplete }: Props) {
  const [newStatus, setNewStatus] = useState(TRANSITIONS[target.status]?.[0] ?? '');
  const [analystName, setAnalystName] = useState('Analyst');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const allowed = TRANSITIONS[target.status] ?? [];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await axios.post(`${API}/api/v1/projects/${projectId}/workspace/targets/${target.id}/verify`, {
        new_status: newStatus,
        verified_by: analystName,
        notes: notes,
      });
      onComplete();
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) setError(err.response?.data?.detail ?? err.message);
      else setError('Failed to verify target');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl w-full max-w-lg shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-zinc-800">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-blue-400" />
            <h2 className="text-lg font-semibold text-zinc-100">Verify Target Status</h2>
          </div>
          <button onClick={onClose} className="text-zinc-500 hover:text-zinc-300">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div className="text-sm text-zinc-400 mb-4">
            Current status: <span className="font-mono text-zinc-200">{target.status}</span>
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-1.5">New Status</label>
            <select
              value={newStatus}
              onChange={e => setNewStatus(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2 text-sm text-zinc-200 focus:border-blue-500 outline-none"
              required
            >
              {allowed.map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-1.5">Verified By</label>
            <input
              type="text"
              value={analystName}
              onChange={e => setAnalystName(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2 text-sm text-zinc-200 focus:border-blue-500 outline-none"
              placeholder="Analyst Name"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-1.5">Verification Notes</label>
            <textarea
              value={notes}
              onChange={e => setNotes(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2 text-sm text-zinc-200 focus:border-blue-500 outline-none h-24 resize-none"
              placeholder="Evidence, findings, or reasons for this transition..."
            />
          </div>

          {error && <div className="text-sm text-red-400 bg-red-500/10 p-3 rounded">{error}</div>}

          <div className="pt-4 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-zinc-400 hover:text-zinc-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !newStatus}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium disabled:opacity-50"
            >
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              Confirm Verification
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
