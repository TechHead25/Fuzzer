export interface AIAnalysisResponsePayload {
  vulnerability_class: string;
  severity: string;
  root_cause_hypothesis: string;
  affected_component: string;
  relevant_code: string;
  explanation: string;
  recommended_investigation: string;
  remediation_guidance: string;
  confidence: string;
  uncertainty: string;
}

export interface AIAnalysisRecord {
  id: number;
  crash_id: number;
  model_name: string;
  model_version: string;
  prompt_version: string;
  evidence_ids: Record<string, unknown> | null;
  response_payload: AIAnalysisResponsePayload;
  reviewer_decision: string;
  reviewer_notes: string | null;
  timestamp: string;
}
