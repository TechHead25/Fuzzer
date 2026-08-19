export interface Project {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
}

export interface Target {
  id: number;
  name: string;
  module: string;
  risk_score: number;
  confidence: number;
  status: string;
  input_type: string;
  project_id: number;
  created_at: string;
}

export interface Campaign {
  id: number;
  project_id: number;
  target_id: number;
  harness_id: number;
  worker_id: number | null;
  fuzzer: string;
  instrumentation: string;
  status: string;
  executions: number;
  start_time: string | null;
  end_time: string | null;
  created_at: string;
}

export interface Crash {
  id: number;
  campaign_id: number;
  target_id: number;
  exception_type: string;
  fault_address: string;
  module: string;
  crash_signature: string;
  reproduction_status: string;
  severity: string;
  vulnerability_class: string;
  created_at: string;
}

export interface Finding {
  id: number;
  project_id: number;
  target_id: number;
  crash_id: number;
  title: string;
  description: string;
  severity: string;
  status: string;
}

export interface Worker {
  id: number;
  hostname: string;
  ip_address: string;
  status: string;
  last_seen: string | null;
  capabilities: Record<string, unknown> | null;
}

export interface DashboardStats {
  active_campaigns: number;
  total_executions: number;
  execs_per_second: number;
  unique_paths: number;
  coverage_percent: number;
  raw_crashes: number;
  unique_crashes: number;
  confirmed_findings: number;
  total_targets: number;
  total_workers: number;
  online_workers: number;
}

export interface RecentActivity {
  id: number;
  entity_type: string;
  entity_id: number;
  message: string;
  timestamp: string;
}

export interface CoverageTrendPoint {
  timestamp: string;
  edges: number;
  blocks: number;
}

export interface ExecutionTrendPoint {
  timestamp: string;
  executions: number;
  execs_per_second: number;
}

export interface CrashTrendPoint {
  timestamp: string;
  total_crashes: number;
  unique_crashes: number;
}

export interface TargetRiskItem {
  name: string;
  module: string;
  risk_score: number;
  status: string;
}

export interface DashboardResponse {
  stats: DashboardStats;
  workers: Worker[];
  recent_activity: RecentActivity[];
  coverage_trend: CoverageTrendPoint[];
  execution_trend: ExecutionTrendPoint[];
  crash_trend: CrashTrendPoint[];
  target_risk_distribution: TargetRiskItem[];
  active_campaigns_list: Campaign[];
}
