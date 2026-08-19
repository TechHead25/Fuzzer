export interface CampaignConfiguration {
  corpus_id: number | null;
  fuzzer_version: string | null;
  instrumentation_version: string | null;
  command_args: Record<string, unknown> | null;
  env_vars: Record<string, unknown> | null;
  timeout: number | null;
  duration_limit_secs: number | null;
  memory_limit: number | null;
  dictionary_path: string | null;
}

export interface CampaignMetric {
  id: number;
  timestamp: string;
  executions: number;
  execs_per_second: number;
  unique_paths: number;
  crashes: number;
  hangs: number;
}

export interface Campaign {
  id: number;
  project_id: number;
  target_id: number;
  harness_id: number;
  worker_id: number | null;
  fuzzer: string;
  instrumentation: string;
  start_time: string | null;
  end_time: string | null;
  status: string;
  executions: number;
  created_at: string;
  configuration: CampaignConfiguration | null;
  metrics: CampaignMetric[];
}

export interface CampaignCreate {
  target_id: number;
  harness_id: number;
  worker_id: number | null;
  fuzzer: string;
  instrumentation: string;
  configuration: CampaignConfiguration;
}

export interface WorkerStatus {
  id: number;
  hostname: string;
  ip_address: string;
  status: string;
  last_seen: string;
  capabilities: {
    status: string;
    os: string;
    memory_available_gb: number;
  } | null;
}
