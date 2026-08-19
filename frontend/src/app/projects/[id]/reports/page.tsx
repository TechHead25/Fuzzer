"use client";
import { use } from 'react';

import { useEffect, useState, useRef } from 'react';
import axios from 'axios';
import { FileText, Download, Printer, LayoutTemplate, Activity } from 'lucide-react';
import clsx from 'clsx';
import { Card, CardHeader } from '@/components/discovery/ui';
import { Report } from '@/types/reports';
import { Campaign } from '@/types/campaigns';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export default function ReportsPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const projectId = Number(resolvedParams.id);
  
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selectedCampaignId, setSelectedCampaignId] = useState<number | null>(null);
  
  const [reports, setReports] = useState<Report[]>([]);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  
  const iframeRef = useRef<HTMLIFrameElement>(null);

  const fetchReports = async () => {
    try {
      const res = await axios.get<Report[]>(`${API}/api/v1/projects/${projectId}/reports`);
      setReports(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchReports();
    
    axios.get<Campaign[]>(`${API}/api/v1/projects/${projectId}/campaigns/`)
      .then(res => setCampaigns(res.data))
      .catch(console.error);
  }, [projectId]);

  const handleGenerate = async () => {
    if (!selectedCampaignId) return;
    try {
      await axios.post(`${API}/api/v1/projects/${projectId}/reports/generate/${selectedCampaignId}`);
      fetchReports();
    } catch (e) {
      console.error(e);
    }
  };

  const handleDownload = (report: Report) => {
    window.location.href = `${API}/api/v1/projects/${projectId}/reports/${report.id}/download`;
  };

  const selectReport = (r: Report) => {
    setSelectedReport(r);
  };
  
  useEffect(() => {
    if (selectedReport && iframeRef.current) {
      const doc = iframeRef.current.contentDocument;
      if (doc) {
        doc.open();
        doc.write(selectedReport.content_html);
        doc.close();
      }
    }
  }, [selectedReport]);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100 flex items-center gap-2">
            <LayoutTemplate className="w-6 h-6 text-fuchsia-500" />
            Security Reports
          </h1>
          <p className="text-sm text-zinc-500 mt-1">Generate and export comprehensive HTML/PDF technical findings.</p>
        </div>
        
        <div className="flex items-center gap-4">
          <select 
            value={selectedCampaignId || ''} 
            onChange={(e) => setSelectedCampaignId(Number(e.target.value))}
            className="bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-sm text-zinc-300 min-w-[200px]"
          >
            <option value="" disabled>Select Campaign...</option>
            {campaigns.map(c => <option key={c.id} value={c.id}>Campaign #{c.id} ({c.status})</option>)}
          </select>
          
          <button 
            onClick={handleGenerate}
            disabled={!selectedCampaignId}
            className="flex items-center gap-2 px-4 py-2 bg-fuchsia-600 hover:bg-fuchsia-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          >
            Generate Report
          </button>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-6">
        
        {/* Left Column: Report Ledger */}
        <div className="col-span-1 space-y-6">
          <Card className="h-[750px] flex flex-col">
            <CardHeader icon={FileText} title="Document Archive" />
            <div className="p-2 overflow-y-auto flex-1 space-y-2">
              {reports.length === 0 ? (
                <div className="text-sm text-zinc-500 p-4 text-center">No reports generated yet.</div>
              ) : (
                reports.map(r => (
                  <div 
                    key={r.id} 
                    onClick={() => selectReport(r)}
                    className={clsx(
                      "p-3 rounded border cursor-pointer transition-colors",
                      selectedReport?.id === r.id 
                        ? "bg-zinc-800 border-fuchsia-500/50" 
                        : "bg-zinc-900 border-zinc-800 hover:border-zinc-700"
                    )}
                  >
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-semibold text-zinc-200">Report #{r.id}</span>
                      <span className="text-xs text-zinc-500">{new Date(r.created_at).toLocaleDateString()}</span>
                    </div>
                    <div className="text-xs text-zinc-400 truncate">{r.title}</div>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>

        {/* Right Column: Preview Pane */}
        <div className="col-span-3 space-y-6">
          {selectedReport ? (
            <Card className="h-[750px] flex flex-col">
              <div className="flex items-center justify-between p-4 border-b border-zinc-800">
                <div className="flex items-center gap-2 text-zinc-100 font-semibold">
                  <Activity className="w-5 h-5 text-fuchsia-400" />
                  Document Preview
                </div>
                <div className="flex gap-2">
                  <button 
                    onClick={() => handleDownload(selectedReport)}
                    className="flex items-center gap-2 text-xs bg-zinc-800 hover:bg-zinc-700 text-zinc-300 px-3 py-1.5 rounded font-medium"
                  >
                    <Download className="w-4 h-4" /> Export HTML
                  </button>
                  <button 
                    onClick={() => {
                      if (iframeRef.current && iframeRef.current.contentWindow) {
                        iframeRef.current.contentWindow.print();
                      }
                    }}
                    className="flex items-center gap-2 text-xs bg-zinc-800 hover:bg-zinc-700 text-zinc-300 px-3 py-1.5 rounded font-medium"
                  >
                    <Printer className="w-4 h-4" /> Print PDF
                  </button>
                </div>
              </div>
              
              <div className="flex-1 bg-white rounded-b-lg overflow-hidden p-2">
                <iframe 
                  ref={iframeRef}
                  className="w-full h-full border-0 bg-white"
                  title="Report Preview"
                />
              </div>
            </Card>
          ) : (
            <div className="h-[750px] flex items-center justify-center text-zinc-500 border border-dashed border-zinc-800 rounded-lg">
              Select a report to preview the document.
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
