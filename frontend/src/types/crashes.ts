export interface CrashSchema {
  id: number;
  campaign_id: number;
  target_id: number;
  worker_id: number | null;
  input_artifact: string;
  minimized_artifact: string | null;
  exception_type: string;
  fault_address: string;
  module: string;
  stack_trace: string;
  crash_signature: string;
  status: string;
  duplicate_of_id: number | null;
  ai_analysis_notes: string | null;
  human_review_notes: string | null;
  severity: string | null;
  vulnerability_class: string | null;
  created_at: string;
}
