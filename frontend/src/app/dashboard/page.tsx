"use client";

import { useEffect, useState } from 'react';
import axios from 'axios';
import { DashboardResponse } from '@/types/models';
import { StatCard } from '@/components/dashboard/StatCard';
import { CoverageChart } from '@/components/dashboard/CoverageChart';
import { ExecutionChart } from '@/components/dashboard/ExecutionChart';
import { CrashChart } from '@/components/dashboard/CrashChart';
import { TargetRiskChart } from '@/components/dashboard/TargetRiskChart';
import { WorkerStatusPanel } from '@/components/dashboard/WorkerStatusPanel';
import { RecentActivityPanel } from '@/components/dashboard/RecentActivityPanel';
import { ActiveCampaignsTable } from '@/components/dashboard/ActiveCampaignsTable';
import { 
  Activity, 
  Zap, 
  Gauge, 
  GitBranch, 
  Shield, 
  AlertTriangle, 
  Fingerprint, 
  ShieldAlert,
  AlertCircle
} from 'lucide-react';

export default function DashboardPage() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        setLoading(true);
        // Assuming api is configured with baseURL in src/lib/api.ts
        // But prompt says to fetch from http://localhost:8000/api/v1/dashboard/
        const response = await axios.get<DashboardResponse>('http://localhost:8000/api/v1/dashboard/');
        setData(response.data);
        setError(null);
      } catch (err: unknown) {
        if (err instanceof Error) {
          setError(err.message || 'Failed to load dashboard data');
        } else {
          setError('Failed to load dashboard data');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, []);

  if (loading) {
    return (
      <div className="p-6 max-w-7xl mx-auto space-y-6 animate-pulse">
        <div className="h-8 bg-zinc-800/50 rounded w-48 mb-6"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => <div key={i} className="h-24 bg-zinc-800/50 rounded-lg"></div>)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {[...Array(4)].map((_, i) => <div key={i} className="h-[350px] bg-zinc-800/50 rounded-lg"></div>)}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-6 flex items-start gap-4 text-red-400">
          <AlertCircle className="w-6 h-6 shrink-0 mt-0.5" />
          <div>
            <h3 className="text-lg font-medium mb-1">Error Loading Dashboard</h3>
            <p className="text-sm text-red-400/80">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="p-6 max-w-[1600px] mx-auto space-y-6">
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-2xl font-bold text-zinc-100">Security Operations</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Active Campaigns" value={data.stats.active_campaigns} icon={Activity} href="/campaigns" />
        <StatCard label="Total Executions" value={data.stats.total_executions} icon={Zap} />
        <StatCard label="Exec Speed" value={data.stats.execs_per_second} icon={Gauge} format="speed" />
        <StatCard label="Unique Paths" value={data.stats.unique_paths} icon={GitBranch} />
        <StatCard label="Coverage" value={data.stats.coverage_percent} icon={Shield} format="percent" />
        <StatCard label="Raw Crashes" value={data.stats.raw_crashes} icon={AlertTriangle} href="/crashes" />
        <StatCard label="Unique Crashes" value={data.stats.unique_crashes} icon={Fingerprint} />
        <StatCard label="Confirmed Findings" value={data.stats.confirmed_findings} icon={ShieldAlert} href="/findings" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <CoverageChart data={data.coverage_trend} />
        <ExecutionChart data={data.execution_trend} />
        <CrashChart data={data.crash_trend} />
        <TargetRiskChart data={data.target_risk_distribution} />
      </div>

      <ActiveCampaignsTable campaigns={data.active_campaigns_list} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <WorkerStatusPanel workers={data.workers} />
        <RecentActivityPanel activities={data.recent_activity} />
      </div>
    </div>
  );
}
