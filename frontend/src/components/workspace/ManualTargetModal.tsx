"use client";

import { useState } from 'react';
import { X, Plus, Loader2 } from 'lucide-react';
import axios from 'axios';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

interface Props {
  projectId: number;
  onClose: () => void;
  onComplete: () => void;
}

export function ManualTargetModal({ projectId, onClose, onComplete }: Props) {
  const [name, setName] = useState('');
  const [moduleName, setModule] = useState('SumatraPDF');
  const [address, setAddress] = useState('');
  const [addressKind, setAddressKind] = useState('user_provided');
  const [riskScore, setRiskScore] = useState(5.0);
  const [notes, setNotes] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await axios.post(`${API}/api/v1/projects/${projectId}/workspace/targets`, {
        name,
        module: moduleName,
        address: address || null,
        address_kind: addressKind,
        risk_score: riskScore,
        confidence: 1.0,
        analyst_notes: notes,
      });
      onComplete();
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) setError(err.response?.data?.detail ?? err.message);
      else setError('Failed to add target');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto py-10">
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl w-full max-w-xl shadow-2xl overflow-hidden my-auto">
        <div className="flex items-center justify-between p-4 border-b border-zinc-800">
          <div className="flex items-center gap-2">
            <Plus className="w-5 h-5 text-emerald-400" />
            <h2 className="text-lg font-semibold text-zinc-100">Add Manual Target</h2>
          </div>
          <button onClick={onClose} className="text-zinc-500 hover:text-zinc-300">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          
          <div className="grid grid-cols-2 gap-5">
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-1.5">Function Name *</label>
              <input
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2 text-sm text-zinc-200 font-mono focus:border-blue-500 outline-none"
                placeholder="e.g. ParseDocumentHeader"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-1.5">Module *</label>
              <input
                type="text"
                value={moduleName}
                onChange={e => setModule(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2 text-sm text-zinc-200 font-mono focus:border-blue-500 outline-none"
                placeholder="e.g. SumatraPDF"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-5">
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-1.5">Address (Hex)</label>
              <input
                type="text"
                value={address}
                onChange={e => setAddress(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2 text-sm text-zinc-200 font-mono focus:border-blue-500 outline-none"
                placeholder="0x..."
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-1.5">Address Evidence Kind</label>
              <select
                value={addressKind}
                onChange={e => setAddressKind(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2 text-sm text-zinc-200 focus:border-blue-500 outline-none"
              >
                <option value="user_provided">User Provided</option>
                <option value="observed">Observed (from binary)</option>
                <option value="inferred">Inferred</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-1.5 flex justify-between">
              Initial Risk Score <span>{riskScore.toFixed(1)}</span>
            </label>
            <input
              type="range"
              min={0} max={10} step={0.5}
              value={riskScore}
              onChange={e => setRiskScore(Number(e.target.value))}
              className="w-full accent-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-1.5">Analyst Notes</label>
            <textarea
              value={notes}
              onChange={e => setNotes(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2 text-sm text-zinc-200 focus:border-blue-500 outline-none h-24 resize-none"
              placeholder="Why is this a good target? Where did you find it?"
            />
          </div>

          {error && <div className="text-sm text-red-400 bg-red-500/10 p-3 rounded border border-red-500/20">{error}</div>}

          <div className="pt-2 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-zinc-400 hover:text-zinc-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !name || !moduleName}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium disabled:opacity-50"
            >
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              Add Target
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
