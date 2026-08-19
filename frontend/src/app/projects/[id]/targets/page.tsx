"use client";
import { use } from 'react';

import { useEffect, useState, useCallback } from 'react';
import { Crosshair, RefreshCw, Filter, Upload, AlertCircle } from 'lucide-react';
import axios from 'axios';
import { TargetSummary } from '@/types/discovery';
import { TargetTable } from '@/components/discovery/TargetTable';
import { SourceUploader } from '@/components/discovery/SourceUploader';
import { Card, CardHeader, EmptyState } from '@/components/discovery/ui';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export default function TargetsPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const projectId = Number(resolvedParams.id);

  const [targets, setTargets] = useState<TargetSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showUploader, setShowUploader] = useState(false);
  const [sortBy, setSortBy] = useState<string>('risk_score');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [minRisk, setMinRisk] = useState(0);

  const fetchTargets = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get<TargetSummary[]>(
        `${API}/api/v1/projects/${projectId}/targets/`,
        { params: { sort_by: sortBy, min_risk: minRisk, limit: 200 } }
      );
      const sorted = [...res.data].sort((a, b) => {
        const av = a[sortBy as keyof TargetSummary] as number;
        const bv = b[sortBy as keyof TargetSummary] as number;
        return sortDir === 'desc' ? bv - av : av - bv;
      });
      setTargets(sorted);
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail ?? err.message);
      } else {
        setError('Failed to load targets');
      }
    } finally {
      setLoading(false);
    }
  }, [projectId, sortBy, minRisk, sortDir]);

  useEffect(() => { fetchTargets(); }, [fetchTargets]);

  const handleSort = (col: string) => {
    if (col === sortBy) setSortDir(d => d === 'desc' ? 'asc' : 'desc');
    else { setSortBy(col); setSortDir('desc'); }
  };

  return (
    <div className="p-6 max-w-[1600px] mx-auto space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Target Discovery</h1>
          <p className="text-sm text-zinc-500 mt-1">
            Static analysis pipeline — all results are from real source analysis, never fabricated
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => fetchTargets()}
            className="inline-flex items-center gap-2 text-sm text-zinc-400 hover:text-zinc-200 transition-colors"
          >
            <RefreshCw className="w-4 h-4" /> Refresh
          </button>
          <button
            onClick={() => setShowUploader(v => !v)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition-colors"
          >
            <Upload className="w-4 h-4" />
            {showUploader ? 'Hide Uploader' : 'Analyze Source'}
          </button>
        </div>
      </div>

      {/* Stats strip */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Total Targets', value: targets.length },
          { label: 'High Risk (≥ 7.5)', value: targets.filter(t => t.risk_score >= 7.5).length },
          { label: 'Pending Harness', value: targets.filter(t => t.status === 'analyzed').length },
        ].map(stat => (
          <div key={stat.label} className="bg-zinc-900/80 border border-zinc-800 rounded-lg px-5 py-4">
            <div className="text-xs text-zinc-500 uppercase tracking-wider mb-1">{stat.label}</div>
            <div className="text-2xl font-bold tabular-nums text-zinc-100">{stat.value}</div>
          </div>
        ))}
      </div>

      {/* Uploader panel */}
      {showUploader && (
        <Card>
          <CardHeader icon={Upload} title="Analyze Source Files" subtitle="Upload a .zip of C/C++ source to run the static analysis pipeline" />
          <div className="p-5">
            <SourceUploader
              projectId={projectId}
              onComplete={() => { setShowUploader(false); fetchTargets(); }}
            />
          </div>
        </Card>
      )}

      {/* Filter bar */}
      <div className="flex items-center gap-4">
        <Filter className="w-4 h-4 text-zinc-500 shrink-0" />
        <label className="text-sm text-zinc-400">Min risk:</label>
        <select
          value={minRisk}
          onChange={e => setMinRisk(Number(e.target.value))}
          className="bg-zinc-900 border border-zinc-700 text-zinc-300 text-sm rounded-md px-3 py-1.5"
        >
          {[0, 1, 2.5, 5, 7.5].map(v => (
            <option key={v} value={v}>{v === 0 ? 'All' : `≥ ${v}`}</option>
          ))}
        </select>
      </div>

      {/* Target table */}
      <Card>
        <CardHeader
          icon={Crosshair}
          title="Ranked Attack Surface"
          subtitle="Sorted by risk score — click a row to see full analysis"
        />

        {error && (
          <div className="m-5 flex items-start gap-3 text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-sm">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {loading ? (
          <div className="p-8 space-y-3 animate-pulse">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-10 bg-zinc-800/40 rounded" />
            ))}
          </div>
        ) : targets.length === 0 ? (
          <EmptyState
            icon={Crosshair}
            title="No targets discovered yet"
            body="Upload a .zip of C/C++ source files and click 'Analyze Source' to begin identifying candidate fuzzing targets. Results appear here after analysis completes."
          />
        ) : (
          <TargetTable
            targets={targets}
            projectId={projectId}
            sortBy={sortBy}
            sortDir={sortDir}
            onSort={handleSort}
          />
        )}
      </Card>
    </div>
  );
}
