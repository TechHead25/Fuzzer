"use client";
import { use } from 'react';

import { useEffect, useState } from 'react';
import axios from 'axios';
import { Target, Activity, ArrowRight, Download, BarChart2 } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import clsx from 'clsx';
import { Card, CardHeader } from '@/components/discovery/ui';
import { CoverageSnapshot, CoverageDelta } from '@/types/coverage';
import { TargetSummary } from '@/types/discovery';
import { Campaign } from '@/types/campaigns';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export default function CoverageDashboardPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const projectId = Number(resolvedParams.id);
  
  const [targets, setTargets] = useState<TargetSummary[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selectedTarget, setSelectedTarget] = useState<number | null>(null);
  
  const [snapshots, setSnapshots] = useState<CoverageSnapshot[]>([]);
  
  const [baselineId, setBaselineId] = useState<number | null>(null);
  const [currentId, setCurrentId] = useState<number | null>(null);
  const [delta, setDelta] = useState<CoverageDelta | null>(null);

  // Load targets and campaigns
  useEffect(() => {
    axios.get<TargetSummary[]>(`${API}/api/v1/projects/${projectId}/targets/`)
      .then(res => {
        const verified = res.data.filter(t => !['DISCOVERED', 'REVIEW_REQUIRED', 'DISABLED'].includes(t.status));
        setTargets(verified);
        if (verified.length > 0) setSelectedTarget(verified[0].id);
      })
      .catch(console.error);
      
    axios.get<Campaign[]>(`${API}/api/v1/projects/${projectId}/campaigns/`)
      .then(res => setCampaigns(res.data))
      .catch(console.error);
  }, [projectId]);

  // Load timeline data when target changes
  useEffect(() => {
    if (!selectedTarget) return;
    
    const fetchTimeline = () => {
      axios.get<CoverageSnapshot[]>(`${API}/api/v1/projects/${projectId}/coverage/timeline?target_id=${selectedTarget}`)
        .then(res => setSnapshots(res.data))
        .catch(console.error);
    };
    
    fetchTimeline();
    const interval = setInterval(fetchTimeline, 5000);
    return () => clearInterval(interval);
  }, [selectedTarget, projectId]);

  // Fetch Delta
  useEffect(() => {
    if (baselineId && currentId && baselineId !== currentId) {
      axios.get<CoverageDelta>(`${API}/api/v1/projects/${projectId}/coverage/compare?baseline_id=${baselineId}&current_id=${currentId}`)
        .then(res => setDelta(res.data))
        .catch(() => setDelta(null));
    } else {
      setDelta(null);
    }
  }, [baselineId, currentId, projectId]);

  const handleExport = () => {
    if (!selectedTarget) return;
    window.location.href = `${API}/api/v1/projects/${projectId}/coverage/export?target_id=${selectedTarget}`;
  };

  const chartData = snapshots.map(s => ({
    time: new Date(s.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    paths: s.unique_paths ?? 0,
    blocks: s.blocks ?? 0
  }));

  const DeltaRow = ({ label, base, curr, diff }: { label: string, base: number | null, curr: number | null, diff: number | null }) => {
    if (base === null || curr === null) {
      return (
        <div className="flex justify-between items-center py-3 border-b border-zinc-800/50">
          <span className="text-zinc-400">{label}</span>
          <span className="text-zinc-500 font-mono text-sm">NOT AVAILABLE</span>
        </div>
      );
    }
    
    return (
      <div className="flex justify-between items-center py-3 border-b border-zinc-800/50">
        <span className="text-zinc-400">{label}</span>
        <div className="flex items-center gap-4 font-mono text-sm">
          <span className="text-zinc-500">{base.toLocaleString()}</span>
          <ArrowRight className="w-3 h-3 text-zinc-600" />
          <span className="text-zinc-100">{curr.toLocaleString()}</span>
          <span className={clsx("w-16 text-right font-bold", (diff || 0) > 0 ? "text-emerald-400" : (diff || 0) < 0 ? "text-red-400" : "text-zinc-500")}>
            {(diff || 0) > 0 ? '+' : ''}{diff}
          </span>
        </div>
      </div>
    );
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Coverage Analytics</h1>
          <p className="text-sm text-zinc-500 mt-1">Independent coverage telemetry and cross-campaign tracking.</p>
        </div>
        
        <div className="flex items-center gap-4">
          <select 
            value={selectedTarget || ''} 
            onChange={(e) => setSelectedTarget(Number(e.target.value))}
            className="bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-sm text-zinc-300 min-w-[200px]"
          >
            <option value="" disabled>Select Target</option>
            {targets.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
          </select>
          
          <button 
            onClick={handleExport}
            disabled={!selectedTarget || snapshots.length === 0}
            className="flex items-center gap-2 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-lg text-sm transition-colors disabled:opacity-50"
          >
            <Download className="w-4 h-4" /> Export CSV
          </button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        
        {/* Timeline Chart */}
        <div className="col-span-2 space-y-6">
          <Card>
            <CardHeader icon={Activity} title="Coverage Growth Timeline" />
            <div className="h-[400px] p-4">
              {snapshots.length === 0 ? (
                <div className="h-full flex items-center justify-center text-zinc-500">No coverage data available for this target.</div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" vertical={false} />
                    <XAxis dataKey="time" stroke="#a1a1aa" fontSize={12} tickMargin={10} />
                    <YAxis yAxisId="left" stroke="#a1a1aa" fontSize={12} />
                    <YAxis yAxisId="right" orientation="right" stroke="#a1a1aa" fontSize={12} />
                    <Tooltip contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a' }} />
                    <Line yAxisId="left" type="stepAfter" dataKey="paths" stroke="#3b82f6" name="Paths" strokeWidth={2} dot={false} isAnimationActive={false} />
                    <Line yAxisId="right" type="stepAfter" dataKey="blocks" stroke="#10b981" name="Blocks" strokeWidth={2} dot={false} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
          </Card>
        </div>

        {/* Delta Comparison */}
        <div className="col-span-1">
          <Card className="h-full">
            <CardHeader icon={BarChart2} title="Delta Comparison" />
            <div className="p-4 space-y-6">
              
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-zinc-500 mb-1">Baseline Campaign</label>
                  <select 
                    value={baselineId || ''} 
                    onChange={e => setBaselineId(Number(e.target.value))}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-sm text-zinc-300"
                  >
                    <option value="" disabled>Select Baseline...</option>
                    {campaigns.filter(c => c.target_id === selectedTarget).map(c => (
                      <option key={c.id} value={c.id}>Campaign #{c.id} ({c.status})</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-xs font-medium text-zinc-500 mb-1">Current Campaign</label>
                  <select 
                    value={currentId || ''} 
                    onChange={e => setCurrentId(Number(e.target.value))}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-sm text-zinc-300"
                  >
                    <option value="" disabled>Select Current...</option>
                    {campaigns.filter(c => c.target_id === selectedTarget && c.id !== baselineId).map(c => (
                      <option key={c.id} value={c.id}>Campaign #{c.id} ({c.status})</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="pt-4 border-t border-zinc-800/50">
                <h3 className="text-sm font-semibold text-zinc-300 mb-2">Metrics Delta</h3>
                {delta ? (
                  <div>
                    <DeltaRow label="Unique Paths" base={delta.baseline_paths} curr={delta.current_paths} diff={delta.delta_paths} />
                    <DeltaRow label="Basic Blocks" base={delta.baseline_blocks} curr={delta.current_blocks} diff={delta.delta_blocks} />
                  </div>
                ) : (
                  <div className="py-8 text-center text-sm text-zinc-500">
                    Select two campaigns to compare coverage differences.
                  </div>
                )}
              </div>

            </div>
          </Card>
        </div>

      </div>
    </div>
  );
}
