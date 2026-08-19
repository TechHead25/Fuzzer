export interface CoverageSnapshot {
  id: number;
  campaign_id: number;
  target_id: number;
  timestamp: string;
  coverage_metric: string;
  unique_paths: number | null;
  blocks: number | null;
  edges: number | null;
  coverage_data: Record<string, unknown> | null;
  artifact_reference: string | null;
}

export interface CoverageDelta {
  baseline_campaign_id: number;
  current_campaign_id: number;
  baseline_paths: number | null;
  current_paths: number | null;
  delta_paths: number | null;
  baseline_blocks: number | null;
  current_blocks: number | null;
  delta_blocks: number | null;
}
