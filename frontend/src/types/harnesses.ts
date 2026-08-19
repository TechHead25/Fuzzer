export interface HarnessBuild {
  id: number;
  harness_id: number;
  compiler: string | null;
  compiler_version: string | null;
  architecture: string | null;
  build_command: string | null;
  stdout: string | null;
  stderr: string | null;
  binary_path: string | null;
  hash: string | null;
  status: string;
  created_at: string;
  updated_at: string | null;
}

export interface Harness {
  id: number;
  project_id: number;
  target_id: number;
  name: string;
  engine: string;
  input_type: string;
  files: Record<string, string> | null;
  metadata_json: Record<string, unknown> | null;
  status: string;
  created_at: string;
  updated_at: string | null;
  builds: HarnessBuild[];
}

export interface HarnessGenerateRequest {
  input_type: string;
  init_code: string;
  cleanup_code: string;
  headers: string[];
}
