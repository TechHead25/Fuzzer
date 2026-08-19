export interface VerificationRecord {
  id: number;
  target_id: number;
  verified_by: string;
  previous_status: string | null;
  new_status: string;
  evidence: string[] | null;
  notes: string | null;
  timestamp: string;
}

export interface WorkspaceOverview {
  project_id: number;
  total_targets: number;
  by_status: Record<string, number>;
  discovered: number;
  review_required: number;
  verified: number;
  harness_ready: number;
  fuzzing_ready: number;
  active: number;
  disabled: number;
  import_sessions: number;
  coverage_by_target: Record<string, number>;
}

export interface ImportFormatDoc {
  import_type: string;
  display_name: string;
  description: string;
  accepted_extensions: string[];
  example_schema: string | null;
  notes: string | null;
}

export interface ImportSessionSummary {
  id: number;
  project_id: number;
  import_type: string;
  filename: string;
  status: string;
  targets_imported: number;
  error_message: string | null;
  result_summary: Record<string, unknown> | null;
  created_at: string;
}
