"use client";
import { use } from 'react';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Play, Square, Pause, RotateCcw, AlertTriangle, Activity, Target, Zap, Clock, Bug } from 'lucide-react';
import axios from 'axios';
import clsx from 'clsx';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

import { Campaign } from '@/types/campaigns';
import { Card, CardHeader } from '@/components/discovery/ui';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export default function CampaignDashboardPage({ params }: { params: Promise<{ id: string, campaign_id: string }> }) {
  const resolvedParams = use(params);
  const projectId = Number(resolvedParams.id);
  const campaignId = Number(resolvedParams.campaign_id);
  const router = useRouter();

  const [campaign, setCampaign] = useState<Campaign | null>(null);

  const fetchCampaign = async () => {
    try {
      const res = await axios.get<Campaign>(`${API}/api/v1/projects/${projectId}/campaigns/${campaignId}`);
      setCampaign(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  // Poll for updates every 3 seconds if active
  useEffect(() => {
    fetchCampaign();
    const interval = setInterval(() => {
      if (campaign?.status === 'RUNNING' || campaign?.status === 'QUEUED') {
        fetchCampaign();
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [projectId, campaignId, campaign?.status]);

  const handleAction = async (action: 'start' | 'pause' | 'stop') => {
    try {
      await axios.post(`${API}/api/v1/projects/${projectId}/campaigns/${campaignId}/${action}`);
      fetchCampaign();
    } catch (e) {
      console.error(e);
    }
  };

  if (!campaign) return <div className="p-8 text-zinc-500 animate-pulse">Loading Campaign Dashboard...</div>;

  const latestMetric = campaign.metrics?.[0] || {
    executions: 0,
    execs_per_second: 0,
    unique_paths: 0,
    crashes: 0,
    hangs: 0
  };

  // Format chart data (reverse so oldest is first for left-to-right timeline)
  const chartData = [...(campaign.metrics || [])].reverse().map(m => ({
    time: new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    executions: m.executions,
    speed: m.execs_per_second,
    paths: m.unique_paths
  }));

  const StatusBadge = () => {
    const s = campaign.status;
    const colors: Record<string, string> = {
      CREATED: 'bg-zinc-800 text-zinc-300',
      QUEUED: 'bg-blue-900/50 text-blue-300',
      RUNNING: 'bg-emerald-900/50 text-emerald-400',
      PAUSED: 'bg-amber-900/50 text-amber-400',
      STOPPING: 'bg-orange-900/50 text-orange-400',
      COMPLETED: 'bg-zinc-800 text-emerald-500',
      FAILED: 'bg-red-900/50 text-red-400'
    };
    return <span className={clsx("px-2.5 py-1 rounded-full text-xs font-semibold", colors[s] || colors.CREATED)}>{s}</span>;
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      
      {/* Header & Controls */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-zinc-100">Campaign #{campaign.id}</h1>
            <StatusBadge />
          </div>
          <p className="text-sm text-zinc-500 mt-1 font-mono">Fuzzer: {campaign.fuzzer} | Worker ID: {campaign.worker_id}</p>
        </div>
        
        <div className="flex gap-2">
          <button 
            onClick={() => handleAction('start')}
            disabled={['RUNNING', 'QUEUED', 'STOPPING', 'COMPLETED'].includes(campaign.status)}
            className="p-2 rounded bg-zinc-900 border border-zinc-800 hover:border-emerald-500 hover:text-emerald-400 disabled:opacity-30 transition-colors"
            title="Start"
          >
            <Play className="w-5 h-5 fill-current" />
          </button>
          <button 
            onClick={() => handleAction('pause')}
            disabled={!['RUNNING', 'QUEUED'].includes(campaign.status)}
            className="p-2 rounded bg-zinc-900 border border-zinc-800 hover:border-amber-500 hover:text-amber-400 disabled:opacity-30 transition-colors"
            title="Pause"
          >
            <Pause className="w-5 h-5 fill-current" />
          </button>
          <button 
            onClick={() => handleAction('stop')}
            disabled={!['RUNNING', 'QUEUED', 'PAUSED'].includes(campaign.status)}
            className="p-2 rounded bg-zinc-900 border border-zinc-800 hover:border-red-500 hover:text-red-400 disabled:opacity-30 transition-colors"
            title="Stop"
          >
            <Square className="w-5 h-5 fill-current" />
          </button>
        </div>
      </div>

      {/* Real-time Metrics Grid */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="p-4 flex items-center gap-4">
          <div className="p-3 bg-blue-500/10 text-blue-400 rounded-lg"><Activity className="w-6 h-6" /></div>
          <div>
            <div className="text-sm text-zinc-400">Total Executions</div>
            <div className="text-2xl font-bold font-mono text-zinc-100">{latestMetric.executions.toLocaleString()}</div>
          </div>
        </Card>
        <Card className="p-4 flex items-center gap-4">
          <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-lg"><Zap className="w-6 h-6" /></div>
          <div>
            <div className="text-sm text-zinc-400">Execs / Sec</div>
            <div className="text-2xl font-bold font-mono text-zinc-100">{latestMetric.execs_per_second.toFixed(1)}</div>
          </div>
        </Card>
        <Card className="p-4 flex items-center gap-4">
          <div className="p-3 bg-purple-500/10 text-purple-400 rounded-lg"><Target className="w-6 h-6" /></div>
          <div>
            <div className="text-sm text-zinc-400">Unique Paths</div>
            <div className="text-2xl font-bold font-mono text-zinc-100">{latestMetric.unique_paths.toLocaleString()}</div>
          </div>
        </Card>
        <Card className="p-4 flex items-center gap-4 border-red-900/50">
          <div className="p-3 bg-red-500/10 text-red-400 rounded-lg"><AlertTriangle className="w-6 h-6" /></div>
          <div>
            <div className="text-sm text-zinc-400">Unique Crashes</div>
            <div className="text-2xl font-bold font-mono text-red-400">{latestMetric.crashes}</div>
          </div>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-2 gap-6">
        <Card>
          <CardHeader icon={Activity} title="Execution Speed Trend" />
          <div className="h-64 p-4">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" vertical={false} />
                <XAxis dataKey="time" stroke="#a1a1aa" fontSize={12} tickMargin={10} />
                <YAxis stroke="#a1a1aa" fontSize={12} />
                <Tooltip contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a' }} />
                <Line type="monotone" dataKey="speed" stroke="#34d399" strokeWidth={2} dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
        <Card>
          <CardHeader icon={Target} title="Path Discovery" />
          <div className="h-64 p-4">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" vertical={false} />
                <XAxis dataKey="time" stroke="#a1a1aa" fontSize={12} tickMargin={10} />
                <YAxis stroke="#a1a1aa" fontSize={12} />
                <Tooltip contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a' }} />
                <Line type="stepAfter" dataKey="paths" stroke="#a78bfa" strokeWidth={2} dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

    </div>
  );
}
