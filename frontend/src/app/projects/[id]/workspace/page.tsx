"use client";
import { use } from 'react';

import { useEffect, useState, useCallback } from 'react';
import { RefreshCw, FileArchive, Plus, Search, ShieldCheck } from 'lucide-react';
import axios from 'axios';
import { WorkspaceOverview } from '@/types/workspace';
import { TargetSummary, TargetDetail } from '@/types/discovery';
import { Card, CardHeader, EmptyState, Badge, riskVariant } from '@/components/discovery/ui';
import { TargetTable } from '@/components/discovery/TargetTable';
import { WorkspaceUploader } from '@/components/workspace/WorkspaceUploader';
import { ManualTargetModal } from '@/components/workspace/ManualTargetModal';
import { VerificationModal } from '@/components/workspace/VerificationModal';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export default function WorkspacePage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const projectId = Number(resolvedParams.id);

  const [overview, setOverview] = useState<WorkspaceOverview | null>(null);
  const [targets, setTargets] = useState<TargetSummary[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [showUploader, setShowUploader] = useState(false);
  const [showManualModal, setShowManualModal] = useState(false);
  
  const [verifyingTargetId, setVerifyingTargetId] = useState<number | null>(null);
  const [verifyingTargetDetail, setVerifyingTargetDetail] = useState<TargetDetail | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [oRes, tRes] = await Promise.all([
        axios.get<WorkspaceOverview>(`${API}/api/v1/projects/${projectId}/workspace/overview`),
        axios.get<TargetSummary[]>(`${API}/api/v1/projects/${projectId}/targets/`, { params: { limit: 200 } }),
      ]);
      setOverview(oRes.data);
      setTargets(tRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleVerifyClick = async (targetId: number) => {
    try {
      const res = await axios.get<TargetDetail>(`${API}/api/v1/projects/${projectId}/targets/${targetId}`);
      setVerifyingTargetDetail(res.data);
      setVerifyingTargetId(targetId);
    } catch (err) {
      console.error("Failed to fetch target details for verification", err);
    }
  };

  return (
    <div className="p-6 max-w-[1600px] mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Target Research Workspace</h1>
          <p className="text-sm text-zinc-500 mt-1">
            Import, verify, and track SumatraPDF research targets with full evidence lineage
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => fetchData()}
            className="inline-flex items-center gap-2 text-sm text-zinc-400 hover:text-zinc-200 transition-colors mr-2"
          >
            <RefreshCw className="w-4 h-4" /> Refresh
          </button>
          <button
            onClick={() => setShowManualModal(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-white text-sm font-medium transition-colors"
          >
            <Plus className="w-4 h-4" /> Add Manual
          </button>
          <button
            onClick={() => setShowUploader(v => !v)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition-colors"
          >
            <FileArchive className="w-4 h-4" /> Import RE Evidence
          </button>
        </div>
      </div>

      {/* Overview Stats */}
      {overview && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <StatCard label="Discovered" value={overview.discovered} color="text-zinc-300" />
          <StatCard label="Review Required" value={overview.review_required} color="text-orange-400" />
          <StatCard label="Verified" value={overview.verified} color="text-blue-400" />
          <StatCard label="Harness Ready" value={overview.harness_ready} color="text-emerald-400" />
          <StatCard label="Active Fuzzing" value={overview.active} color="text-purple-400" />
        </div>
      )}

      {/* Main content grid */}
      <div className="grid grid-cols-3 gap-6">
        
        {/* Left column: Targets */}
        <div className="col-span-2 space-y-6">
          {showUploader && (
            <Card>
              <CardHeader icon={FileArchive} title="Import Research Evidence" subtitle="Populate workspace without fabricating functions" />
              <div className="p-5 border-t border-zinc-800">
                <WorkspaceUploader projectId={projectId} onComplete={() => { setShowUploader(false); fetchData(); }} />
              </div>
            </Card>
          )}

          <Card>
            <CardHeader icon={Search} title="Research Target Backlog" />
            {loading ? (
              <div className="p-10 text-center text-zinc-500 animate-pulse">Loading targets...</div>
            ) : targets.length === 0 ? (
              <EmptyState
                icon={Search}
                title="Workspace Empty"
                body="Import a Ghidra export or RE notes file, or manually add a target to begin your research."
              />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-zinc-800 text-left text-xs font-semibold text-zinc-500 uppercase">
                      <th className="px-4 py-3">Function</th>
                      <th className="px-4 py-3">Risk</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800/60">
                    {targets.map(t => (
                      <tr key={t.id} className="hover:bg-zinc-800/30 transition-colors group">
                        <td className="px-4 py-3">
                          <div className="font-mono text-zinc-200 text-xs">{t.name}</div>
                          <div className="text-[11px] text-zinc-600 mt-0.5">{t.module}</div>
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant={riskVariant(t.risk_score)}>{t.risk_score.toFixed(1)}</Badge>
                        </td>
                        <td className="px-4 py-3">
                          <StatusBadge status={t.status} />
                        </td>
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={() => handleVerifyClick(t.id)}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-medium border border-zinc-700 transition-colors"
                          >
                            <ShieldCheck className="w-3 h-3" /> Verify
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </div>

        {/* Right column: Coverage & Info */}
        <div className="space-y-6">
          <Card>
            <CardHeader title="Target Coverage" subtitle="Max paths discovered per target" />
            <div className="p-5">
              {!overview || Object.keys(overview.coverage_by_target).length === 0 ? (
                <div className="text-sm text-zinc-500 text-center py-4">No coverage data available yet.</div>
              ) : (
                <div className="space-y-3">
                  {Object.entries(overview.coverage_by_target)
                    .sort(([, a], [, b]) => b - a)
                    .map(([name, edges]) => (
                      <div key={name} className="flex items-center justify-between">
                        <span className="text-xs font-mono text-zinc-400 truncate max-w-[150px]">{name}</span>
                        <span className="text-xs font-semibold text-emerald-400 tabular-nums">{edges} edges</span>
                      </div>
                    ))}
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>

      {/* Modals */}
      {showManualModal && (
        <ManualTargetModal
          projectId={projectId}
          onClose={() => setShowManualModal(false)}
          onComplete={() => { setShowManualModal(false); fetchData(); }}
        />
      )}

      {verifyingTargetId && verifyingTargetDetail && (
        <VerificationModal
          projectId={projectId}
          target={verifyingTargetDetail}
          onClose={() => { setVerifyingTargetId(null); setVerifyingTargetDetail(null); }}
          onComplete={() => { setVerifyingTargetId(null); setVerifyingTargetDetail(null); fetchData(); }}
        />
      )}
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="bg-zinc-900/80 border border-zinc-800 rounded-lg px-5 py-4">
      <div className="text-[11px] text-zinc-500 uppercase tracking-wider mb-1">{label}</div>
      <div className={`text-2xl font-bold tabular-nums ${color}`}>{value}</div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    DISCOVERED:      'bg-zinc-800 text-zinc-400 border-zinc-700',
    REVIEW_REQUIRED: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
    VERIFIED:        'bg-blue-500/10 text-blue-400 border-blue-500/20',
    HARNESS_READY:   'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    FUZZING_READY:   'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    ACTIVE:          'bg-purple-500/10 text-purple-400 border-purple-500/20',
    DISABLED:        'bg-red-500/10 text-red-400 border-red-500/20',
  };
  return (
    <span className={`inline-flex px-2 py-0.5 rounded text-[10px] font-medium border ${styles[status] ?? styles.DISCOVERED}`}>
      {status.replace('_', ' ')}
    </span>
  );
}
