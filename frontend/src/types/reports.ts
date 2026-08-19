export interface Report {
  id: number;
  project_id: number;
  campaign_id: number;
  title: string;
  content_html: string;
  report_hash: string;
  created_at: string;
}
