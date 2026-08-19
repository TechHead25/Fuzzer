// Extended types for Phase 3: Target Discovery

export interface TargetSummary {
  id: number;
  project_id: number;
  name: string;
  module: string;
  source_file: string | null;
  source_line: number | null;
  address: string | null;
  input_type: string;
  risk_score: number;
  confidence: number;
  status: string;
  created_at: string;
  updated_at: string | null;
}

export interface ScoringReason {
  indicator: string;
  description: string;
  weight: number;
  evidence_kind: 'observed' | 'inferred' | 'user_provided';
  source_ref: string | null;
}

export interface TargetDetail extends TargetSummary {
  address_kind: string | null;
  risk_reasons: ScoringReason[];
  attacker_controlled_inputs: Array<{ name: string; type: string }>;
  memory_operations: Record<string, string>;
  call_path: Array<{ caller: string; callee: string; evidence_kind: string }>;
  dependencies: string[];
  suggested_harness_type: string;
}

export interface TargetEvidenceRecord {
  id: number;
  entity_type: string;
  entity_id: number;
  hash: string;
  payload: Record<string, unknown>;
  timestamp: string;
}

export interface DiscoveryJobStatus {
  job_id: string;
  status: 'pending' | 'running' | 'complete' | 'error';
  progress: number;
  message: string;
  result: {
    candidates_found: number;
    above_threshold: number;
    saved_to_db: number;
    min_score: number;
  } | null;
  error: string | null;
}
