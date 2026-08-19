"use client";
import { use } from 'react';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { CheckCircle, AlertCircle, Play, Server, Crosshair, Code, FileText, Settings, Loader2 } from 'lucide-react';
import axios from 'axios';

import { TargetSummary } from '@/types/discovery';
import { Harness } from '@/types/harnesses';
import { WorkerStatus, CampaignCreate } from '@/types/campaigns';
import { Card, CardHeader } from '@/components/discovery/ui';
import clsx from 'clsx';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export default function CampaignWizardPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const projectId = Number(resolvedParams.id);
  const router = useRouter();

  const [targets, setTargets] = useState<TargetSummary[]>([]);
  const [harnesses, setHarnesses] = useState<Harness[]>([]);
  const [workers, setWorkers] = useState<WorkerStatus[]>([]);
  
  const [selectedTarget, setSelectedTarget] = useState<TargetSummary | null>(null);
  const [selectedHarness, setSelectedHarness] = useState<Harness | null>(null);
  const [selectedWorker, setSelectedWorker] = useState<WorkerStatus | null>(null);
  
  const [fuzzer, setFuzzer] = useState('winafl');
  const [instrumentation, setInstrumentation] = useState('dynamorio');
  const [timeout, setTimeoutVal] = useState(3600);
  
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Load verified targets
    axios.get<TargetSummary[]>(`${API}/api/v1/projects/${projectId}/targets/`)
      .then(res => setTargets(res.data.filter(t => !['DISCOVERED', 'REVIEW_REQUIRED', 'DISABLED'].includes(t.status))))
      .catch(console.error);
      
    // Load workers
    axios.get<{stats: any, workers: WorkerStatus[]}>(`${API}/api/v1/dashboard/`)
      .then(res => setWorkers(res.data.workers.filter(w => w.status === 'ONLINE')))
      .catch(console.error);
  }, [projectId]);

  useEffect(() => {
    if (selectedTarget) {
      axios.get<Harness[]>(`${API}/api/v1/projects/${projectId}/targets/${selectedTarget.id}/harnesses`)
        .then(res => {
          const validated = res.data.filter(h => ['VALIDATED', 'READY_FOR_FUZZING'].includes(h.status));
          setHarnesses(validated);
          setSelectedHarness(validated.length > 0 ? validated[0] : null);
        })
        .catch(console.error);
    }
  }, [selectedTarget, projectId]);

  const handleSubmit = async () => {
    if (!selectedTarget || !selectedHarness || !selectedWorker) return;
    setSubmitting(true);
    setError(null);
    try {
      const payload: CampaignCreate = {
        target_id: selectedTarget.id,
        harness_id: selectedHarness.id,
        worker_id: selectedWorker.id,
        fuzzer: fuzzer,
        instrumentation: instrumentation,
        configuration: {
          corpus_id: null,
          fuzzer_version: null,
          instrumentation_version: null,
          command_args: {},
          env_vars: {},
          timeout: timeout,
          duration_limit_secs: null,
          memory_limit: 2048,
          dictionary_path: null
        }
      };
      const res = await axios.post(`${API}/api/v1/projects/${projectId}/campaigns/`, payload);
      // Redirect to campaign dashboard
      router.push(`/projects/${projectId}/campaigns/${res.data.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? err.message);
      setSubmitting(false);
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-zinc-100">Create Campaign</h1>
        <p className="text-sm text-zinc-500 mt-1">Configure and launch a new fuzzing campaign on an available Windows worker.</p>
      </div>

      <div className="grid grid-cols-2 gap-6">
        
        {/* Step 1: Target */}
        <Card>
          <CardHeader icon={Crosshair} title="1. Select Verified Target" />
          <div className="p-4 space-y-2 max-h-60 overflow-y-auto">
            {targets.length === 0 ? <p className="text-sm text-zinc-500">No verified targets available.</p> : targets.map(t => (
              <div
                key={t.id}
                onClick={() => setSelectedTarget(t)}
                className={clsx(
                  "p-3 rounded-lg border cursor-pointer text-sm",
                  selectedTarget?.id === t.id ? "bg-blue-600/10 border-blue-500 text-zinc-100" : "bg-zinc-900 border-zinc-800 text-zinc-400 hover:border-zinc-700"
                )}
              >
                <div className="font-mono">{t.name}</div>
                <div className="text-xs text-zinc-500 mt-1">{t.module}</div>
              </div>
            ))}
          </div>
        </Card>

        {/* Step 2: Harness */}
        <Card>
          <CardHeader icon={Code} title="2. Select Validated Harness" />
          <div className="p-4 space-y-2 max-h-60 overflow-y-auto">
            {!selectedTarget ? <p className="text-sm text-zinc-500">Select a target first.</p> : harnesses.length === 0 ? <p className="text-sm text-red-400">No validated harnesses available for this target. Build one in Harness Studio.</p> : harnesses.map(h => (
              <div
                key={h.id}
                onClick={() => setSelectedHarness(h)}
                className={clsx(
                  "p-3 rounded-lg border cursor-pointer text-sm",
                  selectedHarness?.id === h.id ? "bg-blue-600/10 border-blue-500 text-zinc-100" : "bg-zinc-900 border-zinc-800 text-zinc-400 hover:border-zinc-700"
                )}
              >
                <div className="font-mono">{h.name}</div>
                <div className="text-xs text-zinc-500 mt-1">Input: {h.input_type}</div>
              </div>
            ))}
          </div>
        </Card>

        {/* Step 3: Worker */}
        <Card>
          <CardHeader icon={Server} title="3. Select Online Worker" />
          <div className="p-4 space-y-2 max-h-60 overflow-y-auto">
            {workers.length === 0 ? <p className="text-sm text-red-400">No workers online. Start a Windows Fuzz Worker.</p> : workers.map(w => (
              <div
                key={w.id}
                onClick={() => setSelectedWorker(w)}
                className={clsx(
                  "p-3 rounded-lg border cursor-pointer text-sm flex items-center justify-between",
                  selectedWorker?.id === w.id ? "bg-blue-600/10 border-blue-500 text-zinc-100" : "bg-zinc-900 border-zinc-800 text-zinc-400 hover:border-zinc-700"
                )}
              >
                <div>
                  <div className="font-mono">{w.hostname}</div>
                  <div className="text-xs text-zinc-500 mt-1">{w.ip_address}</div>
                </div>
                <div className="flex items-center gap-1.5 text-xs text-emerald-400">
                  <CheckCircle className="w-3 h-3" /> Online
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Step 4: Config */}
        <Card>
          <CardHeader icon={Settings} title="4. Configuration" />
          <div className="p-4 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-zinc-500 mb-1">Fuzzer Engine</label>
                <select value={fuzzer} onChange={e => setFuzzer(e.target.value)} className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-sm text-zinc-300">
                  <option value="winafl">WinAFL</option>
                  <option value="libfuzzer" disabled>LibFuzzer (Coming soon)</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-zinc-500 mb-1">Instrumentation</label>
                <select value={instrumentation} onChange={e => setInstrumentation(e.target.value)} className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-sm text-zinc-300">
                  <option value="dynamorio">DynamoRIO</option>
                  <option value="intelpt" disabled>Intel PT (Coming soon)</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-zinc-500 mb-1">Target Timeout (ms)</label>
              <input type="number" value={timeout} onChange={e => setTimeoutVal(Number(e.target.value))} className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-sm text-zinc-300" />
            </div>
          </div>
        </Card>

      </div>

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-2 text-red-400 text-sm">
          <AlertCircle className="w-4 h-4" /> {error}
        </div>
      )}

      <div className="flex justify-end pt-4">
        <button
          onClick={handleSubmit}
          disabled={!selectedTarget || !selectedHarness || !selectedWorker || submitting}
          className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium disabled:opacity-50 transition-colors"
        >
          {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-current" />}
          Create & Initialize Campaign
        </button>
      </div>

    </div>
  );
}
