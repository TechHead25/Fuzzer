export interface SeedCorpusCreate {
  name: string;
  description: string | null;
}

export interface SeedCorpusResponse {
  id: number;
  project_id: number;
  name: string;
  description: string | null;
  created_at: string;
  
  total_seeds: number;
  total_bytes: number;
  unique_hashes: number;
  coverage_seeds: number;
  crash_seeds: number;
}

export interface SeedSchema {
  id: number;
  corpus_id: number;
  filename: string;
  file_type: string;
  origin: string;
  size: number;
  hash: string;
  metadata_json: Record<string, unknown> | null;
  parent_seed_id: number | null;
  target_id: number | null;
  discovered_coverage: boolean;
  triggered_crash: boolean;
  created_at: string;
}
