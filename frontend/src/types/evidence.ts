export interface EvidenceRecord {
  id: number;
  project_id: number;
  entity_type: string;
  entity_id: number;
  hash: string;
  payload: Record<string, any>;
  timestamp: string;
}

export interface EvidenceVerificationResult {
  status: string;
  stored_hash: string;
  calculated_hash: string;
}
