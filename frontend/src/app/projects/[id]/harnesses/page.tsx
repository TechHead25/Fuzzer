"use client";
import { use } from 'react';

import { useEffect, useState, useCallback } from 'react';
import { ShieldCheck, Play, Code, CheckCircle, FileCode, Beaker, FileBox } from 'lucide-react';
import axios from 'axios';
import { TargetDetail, TargetSummary } from '@/types/discovery';
import { Harness, HarnessGenerateRequest, HarnessBuild } from '@/types/harnesses';
import { Card, CardHeader, EmptyState, Badge, riskVariant } from '@/components/discovery/ui';
import clsx from 'clsx';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export default function HarnessStudioPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const projectId = Number(resolvedParams.id);

  const [targets, setTargets] = useState<TargetSummary[]>([]);
  const [selectedTarget, setSelectedTarget] = useState<TargetSummary | null>(null);
  
  const [harnesses, setHarnesses] = useState<Harness[]>([]);
  const [activeHarness, setActiveHarness] = useState<Harness | null>(null);

  const [inputType, setInputType] = useState('file');
  const [initCode, setInitCode] = useState('');
  const [cleanupCode, setCleanupCode] = useState('');
  
  const [generating, setGenerating] = useState(false);
  const [building, setBuilding] = useState(false);
  
  const [activeTab, setActiveTab] = useState<string>('harness.cpp');

  const fetchTargets = useCallback(async () => {
    try {
      const res = await axios.get<TargetSummary[]>(`${API}/api/v1/projects/${projectId}/targets/`, { params: { limit: 200 } });
      // Only targets that are VERIFIED or higher
      const valid = res.data.filter(t => !['DISCOVERED', 'REVIEW_REQUIRED', 'DISABLED'].includes(t.status));
      setTargets(valid);
      if (valid.length > 0) setSelectedTarget(valid[0]);
    } catch (err) {
      console.error(err);
    }
  }, [projectId]);

  const fetchHarnesses = useCallback(async (targetId: number) => {
    try {
      const res = await axios.get<Harness[]>(`${API}/api/v1/projects/${projectId}/targets/${targetId}/harnesses`);
      setHarnesses(res.data);
      if (res.data.length > 0) {
        setActiveHarness(res.data[0]);
      } else {
        setActiveHarness(null);
      }
    } catch (err) {
      console.error(err);
    }
  }, [projectId]);

  useEffect(() => { fetchTargets(); }, [fetchTargets]);

  useEffect(() => {
    if (selectedTarget) {
      fetchHarnesses(selectedTarget.id);
    }
  }, [selectedTarget, fetchHarnesses]);

  const handleGenerate = async () => {
    if (!selectedTarget) return;
    setGenerating(true);
    try {
      const req: HarnessGenerateRequest = {
        input_type: inputType,
        init_code: initCode,
        cleanup_code: cleanupCode,
        headers: [],
      };
      await axios.post(`${API}/api/v1/projects/${projectId}/targets/${selectedTarget.id}/harness`, req);
      await fetchHarnesses(selectedTarget.id);
    } catch (err) {
      console.error(err);
    } finally {
      setGenerating(false);
    }
  };

  const handleBuild = async () => {
    if (!activeHarness) return;
    setBuilding(true);
    try {
      await axios.post(`${API}/api/v1/projects/${projectId}/harnesses/${activeHarness.id}/build`);
      await fetchHarnesses(selectedTarget!.id);
    } catch (err) {
      console.error(err);
    } finally {
      setBuilding(false);
    }
  };

  const handleMarkReady = async () => {
    if (!activeHarness) return;
    try {
      await axios.patch(`${API}/api/v1/projects/${projectId}/harnesses/${activeHarness.id}/status`, { status: 'READY_FOR_FUZZING' });
      await fetchHarnesses(selectedTarget!.id);
      await fetchTargets();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="p-6 max-w-[1600px] mx-auto h-[calc(100vh-64px)] flex flex-col gap-6">
      
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Harness Studio</h1>
          <p className="text-sm text-zinc-500 mt-1">Generate and validate C/C++ fuzzing scaffolds for verified targets.</p>
        </div>
      </div>

      <div className="flex gap-6 flex-1 min-h-0">
        
        {/* Left Column: Target Selector & Generator */}
        <div className="w-80 flex flex-col gap-4 overflow-y-auto shrink-0 pr-2">
          
          <div className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-2">Verified Targets</div>
          {targets.map(t => (
            <div
              key={t.id}
              onClick={() => setSelectedTarget(t)}
              className={clsx(
                "p-3 rounded-lg border cursor-pointer transition-colors",
                selectedTarget?.id === t.id
                  ? "bg-blue-600/10 border-blue-500 text-zinc-100"
                  : "bg-zinc-900 border-zinc-800 text-zinc-300 hover:border-zinc-700"
              )}
            >
              <div className="font-mono text-sm truncate">{t.name}</div>
              <div className="flex justify-between items-center mt-2 text-xs">
                <span className="text-zinc-500">{t.module}</span>
                <Badge variant={riskVariant(t.risk_score)}>Risk: {t.risk_score.toFixed(1)}</Badge>
              </div>
            </div>
          ))}
          {targets.length === 0 && (
            <div className="p-4 text-center text-sm text-zinc-500 bg-zinc-900 rounded-lg border border-zinc-800">
              No verified targets available. Go to the Workspace to verify a target first.
            </div>
          )}
          
        </div>

        {/* Right Column: Active Harness */}
        <div className="flex-1 flex flex-col gap-6 min-w-0">
          
          {selectedTarget ? (
            <div className="flex flex-col h-full bg-zinc-950 border border-zinc-800 rounded-xl overflow-hidden shadow-2xl">
              
              {/* Top Bar: Generate Form */}
              <div className="bg-zinc-900 p-4 border-b border-zinc-800 flex items-end gap-4 shrink-0">
                <div className="flex-1">
                  <label className="block text-xs font-medium text-zinc-500 mb-1">Input Strategy</label>
                  <select 
                    value={inputType} 
                    onChange={e => setInputType(e.target.value)}
                    className="w-full bg-zinc-950 border border-zinc-700 rounded px-3 py-1.5 text-sm text-zinc-200 outline-none"
                  >
                    <option value="file">File (Write temp file)</option>
                    <option value="memory_buffer">Memory Buffer (Null terminated)</option>
                    <option value="buffer_and_length">Buffer + Length</option>
                  </select>
                </div>
                <div className="flex-1">
                  <label className="block text-xs font-medium text-zinc-500 mb-1">Init Hook (Optional)</label>
                  <input 
                    type="text" 
                    value={initCode} 
                    onChange={e => setInitCode(e.target.value)}
                    placeholder="e.g. library_init();"
                    className="w-full bg-zinc-950 border border-zinc-700 rounded px-3 py-1.5 text-sm text-zinc-200 font-mono outline-none"
                  />
                </div>
                <div className="flex-1">
                  <label className="block text-xs font-medium text-zinc-500 mb-1">Cleanup Hook (Optional)</label>
                  <input 
                    type="text" 
                    value={cleanupCode} 
                    onChange={e => setCleanupCode(e.target.value)}
                    placeholder="e.g. library_cleanup();"
                    className="w-full bg-zinc-950 border border-zinc-700 rounded px-3 py-1.5 text-sm text-zinc-200 font-mono outline-none"
                  />
                </div>
                <button
                  onClick={handleGenerate}
                  disabled={generating}
                  className="px-6 py-2 rounded bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium disabled:opacity-50 transition-colors h-[34px]"
                >
                  {generating ? "Generating..." : "Generate Harness"}
                </button>
              </div>

              {/* Code Explorer */}
              {activeHarness && activeHarness.files ? (
                <div className="flex flex-1 min-h-0">
                  {/* File Tree Sidebar */}
                  <div className="w-48 bg-zinc-900 border-r border-zinc-800 p-2 overflow-y-auto">
                    {Object.keys(activeHarness.files).map(filename => (
                      <button
                        key={filename}
                        onClick={() => setActiveTab(filename)}
                        className={clsx(
                          "w-full flex items-center gap-2 px-3 py-2 rounded text-sm font-mono text-left transition-colors mb-1",
                          activeTab === filename ? "bg-zinc-800 text-blue-400" : "text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200"
                        )}
                      >
                        <FileCode className="w-4 h-4" />
                        {filename}
                      </button>
                    ))}
                  </div>
                  
                  {/* Editor View */}
                  <div className="flex-1 flex flex-col min-w-0 bg-[#1e1e1e]">
                    <div className="px-4 py-2 bg-zinc-900/50 border-b border-zinc-800 flex justify-between items-center text-xs font-mono text-zinc-400">
                      <span>{activeTab}</span>
                      <span>{activeHarness.status}</span>
                    </div>
                    <div className="flex-1 overflow-auto p-4">
                      <pre className="text-sm font-mono text-zinc-300 whitespace-pre-wrap">
                        {activeHarness.files[activeTab] ?? "// File not found"}
                      </pre>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex-1 flex items-center justify-center text-zinc-500 flex-col gap-4">
                  <FileBox className="w-12 h-12 text-zinc-700" />
                  <p>No harness generated for this target yet.</p>
                </div>
              )}

              {/* Build Console Pane */}
              {activeHarness && (
                <div className="h-64 shrink-0 bg-zinc-950 border-t border-zinc-800 flex flex-col">
                  <div className="bg-zinc-900 px-4 py-2 flex items-center justify-between border-b border-zinc-800">
                    <div className="flex items-center gap-2 text-sm font-medium text-zinc-300">
                      <Beaker className="w-4 h-4 text-emerald-400" /> Validation & Build Console
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={handleBuild}
                        disabled={building}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded text-xs font-medium text-zinc-200 transition-colors disabled:opacity-50"
                      >
                        <Play className="w-3 h-3" />
                        {building ? "Building..." : "Build & Validate locally"}
                      </button>
                      
                      <button
                        onClick={handleMarkReady}
                        disabled={activeHarness.status !== 'VALIDATED'}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600/10 hover:bg-emerald-600/20 border border-emerald-500/20 text-emerald-400 rounded text-xs font-medium transition-colors disabled:opacity-50 disabled:grayscale"
                      >
                        <CheckCircle className="w-3 h-3" />
                        Mark Ready for Fuzzing
                      </button>
                    </div>
                  </div>
                  <div className="flex-1 overflow-y-auto p-4 font-mono text-[11px] leading-relaxed">
                    {activeHarness.builds.length > 0 ? (
                      <div className="space-y-4">
                        {activeHarness.builds[0].stdout?.split('\n').map((line, i) => (
                          <div key={i} className="text-zinc-400">{line}</div>
                        ))}
                        {activeHarness.builds[0].stderr?.split('\n').map((line, i) => (
                          <div key={`err-${i}`} className="text-red-400">{line}</div>
                        ))}
                        {activeHarness.builds[0].status === 'SUCCESS' && (
                          <div className="text-emerald-400 mt-2 font-bold">✓ Build SUCCESS (Hash: {activeHarness.builds[0].hash?.substring(0, 8)})</div>
                        )}
                        {activeHarness.builds[0].status === 'FAILED' && (
                          <div className="text-red-400 mt-2 font-bold">✗ Build FAILED</div>
                        )}
                      </div>
                    ) : (
                      <div className="text-zinc-600 text-center mt-10">Run build to see output</div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center border border-zinc-800 rounded-xl bg-zinc-950/50">
              <EmptyState
                icon={Code}
                title="Harness Studio"
                body="Select a verified target from the backlog to design and build its fuzzing harness."
              />
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
