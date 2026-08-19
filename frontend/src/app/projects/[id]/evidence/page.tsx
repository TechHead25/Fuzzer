"use client";
import { use } from 'react';

import { useEffect, useState } from 'react';
import axios from 'axios';
import { ShieldCheck, ShieldAlert, FileText, CheckCircle, XCircle, ChevronDown, ChevronRight, Fingerprint, Database, Network } from 'lucide-react';
import clsx from 'clsx';
import { Card, CardHeader } from '@/components/discovery/ui';
import { EvidenceRecord, EvidenceVerificationResult } from '@/types/evidence';
import { Campaign } from '@/types/campaigns';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export default function EvidenceLedgerPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const projectId = Number(resolvedParams.id);
  
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selectedCampaignId, setSelectedCampaignId] = useState<number | null>(null);
  
  const [evidenceRecords, setEvidenceRecords] = useState<EvidenceRecord[]>([]);
  const [selectedRecord, setSelectedRecord] = useState<EvidenceRecord | null>(null);
  const [verificationResult, setVerificationResult] = useState<EvidenceVerificationResult | null>(null);

  const fetchEvidence = async () => {
    try {
      const res = await axios.get<EvidenceRecord[]>(`${API}/api/v1/projects/${projectId}/evidence`);
      setEvidenceRecords(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchEvidence();
    
    // Fetch campaigns for the dropdown
    axios.get<Campaign[]>(`${API}/api/v1/projects/${projectId}/campaigns/`)
      .then(res => setCampaigns(res.data))
      .catch(console.error);
  }, [projectId]);

  const handleGenerate = async () => {
    if (!selectedCampaignId) return;
    try {
      await axios.post(`${API}/api/v1/projects/${projectId}/evidence/generate/${selectedCampaignId}`);
      fetchEvidence();
    } catch (e) {
      console.error(e);
    }
  };

  const handleVerify = async (recordId: number) => {
    try {
      const res = await axios.post<EvidenceVerificationResult>(`${API}/api/v1/projects/${projectId}/evidence/verify/${recordId}`);
      setVerificationResult(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const selectRecord = (r: EvidenceRecord) => {
    setSelectedRecord(r);
    setVerificationResult(null); // Reset verification when switching records
  };

  const JsonTree = ({ data, level = 0 }: { data: any, level?: number }) => {
    if (typeof data !== 'object' || data === null) {
      return <span className="text-emerald-400 font-mono">{String(data)}</span>;
    }
    
    return (
      <div className="pl-4 border-l border-zinc-800/50 space-y-1">
        {Object.entries(data).map(([key, val]) => (
          <div key={key}>
            <span className="text-zinc-500">{key}: </span>
            <JsonTree data={val} level={level + 1} />
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100 flex items-center gap-2">
            <Database className="w-6 h-6 text-indigo-500" />
            Evidence Ledger
          </h1>
          <p className="text-sm text-zinc-500 mt-1">Immutable snapshots of security campaign relationships and artifact hashes.</p>
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
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          >
            Generate Snapshot
          </button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        
        {/* Left Column: Ledger List */}
        <div className="col-span-1 space-y-6">
          <Card className="h-[600px] flex flex-col">
            <CardHeader icon={FileText} title="Generated Ledgers" />
            <div className="p-2 overflow-y-auto flex-1 space-y-2">
              {evidenceRecords.length === 0 ? (
                <div className="text-sm text-zinc-500 p-4 text-center">No evidence records exist.</div>
              ) : (
                evidenceRecords.map(r => (
                  <div 
                    key={r.id} 
                    onClick={() => selectRecord(r)}
                    className={clsx(
                      "p-3 rounded border cursor-pointer transition-colors",
                      selectedRecord?.id === r.id 
                        ? "bg-zinc-800 border-indigo-500/50" 
                        : "bg-zinc-900 border-zinc-800 hover:border-zinc-700"
                    )}
                  >
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-semibold text-zinc-200">Snapshot #{r.id}</span>
                      <span className="text-xs text-zinc-500">{new Date(r.timestamp).toLocaleDateString()}</span>
                    </div>
                    <div className="text-xs text-zinc-400">Campaign #{r.entity_id}</div>
                    <div className="mt-2 text-[10px] font-mono text-zinc-600 truncate">{r.hash}</div>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>

        {/* Right Column: Inspector */}
        <div className="col-span-2 space-y-6">
          {selectedRecord ? (
            <>
              <Card>
                <div className="flex items-center justify-between p-4 border-b border-zinc-800">
                  <div className="flex items-center gap-2 text-zinc-100 font-semibold">
                    <Fingerprint className="w-5 h-5 text-indigo-400" />
                    Integrity Verification
                  </div>
                  <button 
                    onClick={() => handleVerify(selectedRecord.id)}
                    className="text-xs bg-zinc-800 hover:bg-zinc-700 text-zinc-300 px-3 py-1.5 rounded font-medium"
                  >
                    Verify Integrity
                  </button>
                </div>
                
                <div className="p-6">
                  {verificationResult ? (
                    <div className={clsx("p-4 rounded border flex items-start gap-4",
                      verificationResult.status === 'VERIFIED' ? "bg-emerald-900/10 border-emerald-900/30" : "bg-red-900/10 border-red-900/30"
                    )}>
                      {verificationResult.status === 'VERIFIED' ? (
                        <ShieldCheck className="w-8 h-8 text-emerald-500 shrink-0" />
                      ) : (
                        <ShieldAlert className="w-8 h-8 text-red-500 shrink-0" />
                      )}
                      
                      <div className="space-y-2 w-full">
                        <div className={clsx("font-semibold", 
                          verificationResult.status === 'VERIFIED' ? "text-emerald-400" : "text-red-400"
                        )}>
                          {verificationResult.status === 'VERIFIED' ? "Cryptographic Match Verified" : "INTEGRITY MISMATCH DETECTED"}
                        </div>
                        <div className="space-y-1">
                          <div className="text-xs text-zinc-500">Stored SHA-256</div>
                          <div className="text-xs font-mono text-zinc-300 bg-zinc-950 p-1.5 rounded border border-zinc-800 break-all">{verificationResult.stored_hash}</div>
                        </div>
                        <div className="space-y-1">
                          <div className="text-xs text-zinc-500">Calculated Payload SHA-256</div>
                          <div className="text-xs font-mono text-zinc-300 bg-zinc-950 p-1.5 rounded border border-zinc-800 break-all">{verificationResult.calculated_hash}</div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-sm text-zinc-500 text-center py-8">
                      Click "Verify Integrity" to securely hash the underlying artifact graph and compare it to the stored signature.
                    </div>
                  )}
                </div>
              </Card>

              <Card className="flex-1">
                <CardHeader icon={Network} title="Artifact Relationship Chain" />
                <div className="p-6 bg-zinc-950 rounded-b-lg overflow-x-auto text-xs leading-loose">
                  <JsonTree data={selectedRecord.payload} />
                </div>
              </Card>
            </>
          ) : (
            <div className="h-[600px] flex items-center justify-center text-zinc-500 border border-dashed border-zinc-800 rounded-lg">
              Select a ledger snapshot to inspect the artifact chain.
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
