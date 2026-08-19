"use client";
import { use } from 'react';

import { useEffect, useState } from 'react';
import axios from 'axios';
import clsx from 'clsx';
import { ShieldAlert, AlertTriangle, Cpu, Terminal, FileCode, CheckCircle, Crosshair, Users, Bot, RefreshCw, ChevronRight, AlertOctagon, XCircle } from 'lucide-react';
import { Card, CardHeader } from '@/components/discovery/ui';
import { CrashSchema } from '@/types/crashes';
import { AIAnalysisRecord } from '@/types/ai';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export default function CrashDetailPage({ params }: { params: Promise<{ id: string, crash_id: string }> }) {
  const resolvedParams = use(params);
  const projectId = Number(resolvedParams.id);
  const crashId = Number(resolvedParams.crash_id);
  
  const [crash, setCrash] = useState<CrashSchema | null>(null);
  const [duplicates, setDuplicates] = useState<CrashSchema[]>([]);
  
  const [aiRecords, setAiRecords] = useState<AIAnalysisRecord[]>([]);
  const [selectedAiRecord, setSelectedAiRecord] = useState<AIAnalysisRecord | null>(null);
  const [aiReviewNote, setAiReviewNote] = useState('');

  const fetchCrashData = async () => {
    try {
      const res = await axios.get<CrashSchema>(`${API}/api/v1/projects/${projectId}/crashes/${crashId}`);
      setCrash(res.data);
      
      const dupRes = await axios.get<CrashSchema[]>(`${API}/api/v1/projects/${projectId}/crashes/${crashId}/duplicates`);
      setDuplicates(dupRes.data);
      
      const aiRes = await axios.get<AIAnalysisRecord[]>(`${API}/api/v1/projects/${projectId}/crashes/${crashId}/analyses`);
      setAiRecords(aiRes.data);
      if (aiRes.data.length > 0 && !selectedAiRecord) {
        setSelectedAiRecord(aiRes.data[0]);
        setAiReviewNote(aiRes.data[0].reviewer_notes || '');
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchCrashData();
  }, [projectId, crashId]);

  const handleAction = async (action: string, notes?: string) => {
    try {
      await axios.post(`${API}/api/v1/projects/${projectId}/crashes/${crashId}/action`, { action, notes });
      fetchCrashData();
    } catch (e) {
      console.error(e);
    }
  };
  
  const handleAiAnalyze = async () => {
    try {
      await axios.post(`${API}/api/v1/projects/${projectId}/crashes/${crashId}/analyze`);
      fetchCrashData();
    } catch (e) {
      console.error(e);
    }
  };
  
  const handleAiReview = async (decision: string) => {
    if (!selectedAiRecord) return;
    try {
      await axios.post(`${API}/api/v1/projects/${projectId}/analyses/${selectedAiRecord.id}/review`, { 
        decision, 
        notes: aiReviewNote 
      });
      fetchCrashData();
      
      // Auto-update crash status based on decision
      if (decision === 'APPROVED') {
        await handleAction('confirm', aiReviewNote);
      }
    } catch (e) {
      console.error(e);
    }
  };

  if (!crash) return <div className="p-8 text-zinc-500 animate-pulse">Loading Crash Details...</div>;

  const StatusBadge = () => {
    const colors: Record<string, string> = {
      DETECTED: 'bg-zinc-800 text-zinc-300',
      REPRODUCING: 'bg-blue-900/50 text-blue-400',
      REPRODUCED: 'bg-emerald-900/50 text-emerald-400',
      NOT_REPRODUCED: 'bg-red-900/50 text-red-400',
      MINIMIZING: 'bg-purple-900/50 text-purple-400',
      MINIMIZED: 'bg-fuchsia-900/50 text-fuchsia-400',
      DUPLICATE: 'bg-zinc-800 text-zinc-500',
      REVIEW_REQUIRED: 'bg-amber-900/50 text-amber-400',
      CONFIRMED: 'bg-emerald-600 text-white',
      REJECTED: 'bg-zinc-800 text-zinc-600 line-through'
    };
    return <span className={clsx("px-3 py-1 rounded-full text-xs font-semibold tracking-wider", colors[crash.status] || colors.DETECTED)}>{crash.status}</span>;
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-bold text-zinc-100 flex items-center gap-2">
              <ShieldAlert className="w-6 h-6 text-red-500" />
              Crash #{crash.id}
            </h1>
            <StatusBadge />
          </div>
          <div className="font-mono text-xs text-zinc-500 bg-zinc-900 px-3 py-1.5 rounded-md inline-block border border-zinc-800">
            Sig: {crash.crash_signature}
          </div>
        </div>
        
        <div className="flex gap-2">
          <button 
            onClick={() => handleAction('reproduce')}
            disabled={!['DETECTED', 'NOT_REPRODUCED'].includes(crash.status)}
            className="flex items-center gap-2 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded text-sm font-medium disabled:opacity-50"
          >
            <RefreshCw className="w-4 h-4" /> Reproduce
          </button>
          <button 
            onClick={() => handleAction('minimize')}
            disabled={!['REPRODUCED'].includes(crash.status)}
            className="flex items-center gap-2 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded text-sm font-medium disabled:opacity-50"
          >
            <Crosshair className="w-4 h-4" /> Minimize
          </button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        
        {/* Left Column: Context & Trace */}
        <div className="col-span-2 space-y-6">
          <Card>
            <CardHeader icon={AlertTriangle} title="Execution Context" />
            <div className="p-4 grid grid-cols-2 gap-4">
              <div>
                <div className="text-xs text-zinc-500 mb-1">Exception Type</div>
                <div className="font-mono text-red-400 text-sm">{crash.exception_type}</div>
              </div>
              <div>
                <div className="text-xs text-zinc-500 mb-1">Fault Address</div>
                <div className="font-mono text-zinc-300 text-sm">{crash.fault_address}</div>
              </div>
              <div>
                <div className="text-xs text-zinc-500 mb-1">Module</div>
                <div className="font-mono text-zinc-300 text-sm">{crash.module}</div>
              </div>
              <div>
                <div className="text-xs text-zinc-500 mb-1">Campaign ID</div>
                <div className="font-mono text-zinc-300 text-sm">{crash.campaign_id}</div>
              </div>
            </div>
          </Card>

          <Card>
            <CardHeader icon={Terminal} title="Stack Trace" />
            <div className="p-4 bg-zinc-950 font-mono text-xs text-zinc-400 whitespace-pre-wrap rounded-b-lg border-t border-zinc-900 overflow-x-auto">
              {crash.stack_trace}
            </div>
          </Card>
          
          <Card>
            <CardHeader icon={FileCode} title="Artifacts" />
            <div className="p-4 space-y-4">
              <div className="flex items-center justify-between p-3 bg-zinc-900/50 rounded border border-zinc-800">
                <div className="flex items-center gap-3">
                  <FileCode className="w-5 h-5 text-zinc-500" />
                  <div>
                    <div className="text-sm font-medium text-zinc-200">Original Input</div>
                    <div className="text-xs text-zinc-500 font-mono mt-1">{crash.input_artifact}</div>
                  </div>
                </div>
                <button className="px-3 py-1 bg-zinc-800 hover:bg-zinc-700 text-xs rounded text-zinc-300">Download</button>
              </div>
              
              {crash.minimized_artifact && (
                <div className="flex items-center justify-between p-3 bg-fuchsia-900/10 rounded border border-fuchsia-900/30">
                  <div className="flex items-center gap-3">
                    <Crosshair className="w-5 h-5 text-fuchsia-500" />
                    <div>
                      <div className="text-sm font-medium text-fuchsia-200">Minimized Input</div>
                      <div className="text-xs text-fuchsia-500/70 font-mono mt-1">{crash.minimized_artifact}</div>
                    </div>
                  </div>
                  <button className="px-3 py-1 bg-fuchsia-900/30 hover:bg-fuchsia-900/50 text-xs rounded text-fuchsia-300">Download</button>
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Right Column: Intelligence & Review */}
        <div className="col-span-1 space-y-6">
          <Card>
            <div className="flex items-center justify-between p-4 border-b border-zinc-800">
              <div className="flex items-center gap-2 text-zinc-100 font-semibold">
                <Bot className="w-5 h-5" /> AI Expert Analysis
              </div>
              <button 
                onClick={handleAiAnalyze} 
                className="text-xs bg-blue-900/30 hover:bg-blue-900/50 text-blue-400 px-3 py-1 rounded"
              >
                {aiRecords.length > 0 ? "Re-analyze" : "Analyze"}
              </button>
            </div>
            
            <div className="bg-amber-900/20 border-b border-amber-900/30 p-3 flex gap-3 items-start">
              <AlertOctagon className="w-5 h-5 text-amber-500 shrink-0" />
              <div className="text-xs text-amber-400/90 leading-relaxed">
                <span className="font-semibold block mb-1">AI-assisted analysis. Human security review required.</span>
                Analyses generated by the platform represent potential vulnerabilities. They must not be treated as confirmed until verified.
              </div>
            </div>

            <div className="p-4 space-y-4">
              {aiRecords.length > 0 && selectedAiRecord ? (
                <>
                  <div className="flex items-center justify-between">
                    <select 
                      className="bg-zinc-950 border border-zinc-800 rounded px-2 py-1 text-xs text-zinc-300"
                      value={selectedAiRecord.id}
                      onChange={e => {
                        const rec = aiRecords.find(r => r.id === Number(e.target.value));
                        if(rec) {
                          setSelectedAiRecord(rec);
                          setAiReviewNote(rec.reviewer_notes || '');
                        }
                      }}
                    >
                      {aiRecords.map((r, i) => (
                        <option key={r.id} value={r.id}>
                          Run {aiRecords.length - i} ({new Date(r.timestamp).toLocaleTimeString()})
                        </option>
                      ))}
                    </select>
                    
                    <span className={clsx("text-xs font-semibold px-2 py-1 rounded", 
                      selectedAiRecord.reviewer_decision === 'APPROVED' ? "bg-emerald-900/30 text-emerald-400" :
                      selectedAiRecord.reviewer_decision === 'REJECTED' ? "bg-red-900/30 text-red-400" :
                      "bg-zinc-800 text-zinc-400"
                    )}>
                      {selectedAiRecord.reviewer_decision}
                    </span>
                  </div>
                
                  <div className="space-y-4 text-sm">
                    <div>
                      <div className="text-xs font-semibold text-zinc-500 mb-1 uppercase tracking-wider">Classification</div>
                      <div className="text-zinc-200 font-medium">{selectedAiRecord.response_payload.vulnerability_class}</div>
                      <div className={clsx("text-xs mt-1 font-semibold", 
                        selectedAiRecord.response_payload.severity === 'High' ? "text-red-400" :
                        selectedAiRecord.response_payload.severity === 'Medium' ? "text-amber-400" : "text-zinc-400"
                      )}>
                        Severity: {selectedAiRecord.response_payload.severity}
                      </div>
                    </div>
                    
                    <div>
                      <div className="text-xs font-semibold text-zinc-500 mb-1 uppercase tracking-wider">Root Cause Hypothesis</div>
                      <div className="text-zinc-300 leading-relaxed">{selectedAiRecord.response_payload.root_cause_hypothesis}</div>
                    </div>
                    
                    <div>
                      <div className="text-xs font-semibold text-zinc-500 mb-1 uppercase tracking-wider">Explanation</div>
                      <div className="text-zinc-400 text-xs leading-relaxed">{selectedAiRecord.response_payload.explanation}</div>
                    </div>
                    
                    <div className="bg-zinc-950 p-3 rounded border border-zinc-900">
                      <div className="text-xs font-semibold text-zinc-500 mb-2 uppercase tracking-wider">Remediation</div>
                      <div className="text-zinc-300 text-xs leading-relaxed">{selectedAiRecord.response_payload.remediation_guidance}</div>
                    </div>
                  </div>
                  
                  <div className="pt-4 border-t border-zinc-800">
                    <div className="text-xs font-semibold text-zinc-500 mb-2 uppercase tracking-wider">Reviewer Action</div>
                    <textarea 
                      value={aiReviewNote} 
                      onChange={e => setAiReviewNote(e.target.value)}
                      placeholder="Analyst verification notes..."
                      className="w-full h-20 bg-zinc-950 border border-zinc-800 rounded p-2 text-xs text-zinc-300 resize-none focus:outline-none focus:border-blue-500 mb-2"
                    />
                    <div className="flex gap-2">
                      <button 
                        onClick={() => handleAiReview('APPROVED')}
                        className="flex-1 px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-medium flex items-center justify-center gap-1"
                      >
                        <CheckCircle className="w-3 h-3" /> Approve & Confirm
                      </button>
                      <button 
                        onClick={() => handleAiReview('REJECTED')}
                        className="flex-1 px-3 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded text-xs font-medium flex items-center justify-center gap-1"
                      >
                        <XCircle className="w-3 h-3" /> Reject
                      </button>
                    </div>
                  </div>
                </>
              ) : (
                <div className="text-sm text-zinc-500 text-center py-8">
                  Run an AI analysis to get a root cause hypothesis and remediation steps.
                </div>
              )}
            </div>
          </Card>
          
          <Card>
            <CardHeader icon={Cpu} title={`Duplicates (${duplicates.length})`} />
            <div className="p-4 max-h-48 overflow-y-auto space-y-2">
              {duplicates.length === 0 ? (
                <div className="text-sm text-zinc-500 text-center">No duplicates found for this signature.</div>
              ) : (
                duplicates.map(d => (
                  <div key={d.id} className="flex items-center justify-between p-2 rounded bg-zinc-900 border border-zinc-800 text-xs">
                    <span className="font-mono text-zinc-400">Crash #{d.id}</span>
                    <span className="text-zinc-600">{new Date(d.created_at).toLocaleDateString()}</span>
                  </div>
                ))
              )}
            </div>
          </Card>

        </div>
      </div>
    </div>
  );
}
