"use client";
import { use } from 'react';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft, Crosshair, Shield, AlertCircle, FileCode,
  GitBranch, Code2, Lock, BookOpen
} from 'lucide-react';
import axios from 'axios';
import { TargetDetail, TargetEvidenceRecord } from '@/types/discovery';
import {
  Badge, EvidenceBadge, Code, riskVariant,
  Card, CardHeader, EmptyState
} from '@/components/discovery/ui';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

const HARNESS_LABELS: Record<string, string> = {
  file_reader:   'File Reader',
  network_stub:  'Network Stub',
  api_fuzzer:    'API Fuzzer',
  format_parser: 'Format Parser',
};

function RiskBreakdownRow({ indicator, weight, description, evidence_kind, source_ref }: {
  indicator: string;
  weight: number;
  description: string;
  evidence_kind: 'observed' | 'inferred' | 'user_provided';
  source_ref: string | null;
}) {
  return (
    <div className="flex items-start gap-4 py-3 border-b border-zinc-800/60 last:border-0">
      <div className="w-20 shrink-0 text-right">
        <span className={`text-sm font-mono font-semibold ${weight >= 1.5 ? 'text-red-400' : weight >= 1.0 ? 'text-orange-400' : 'text-zinc-400'}`}>
          +{weight.toFixed(1)}
        </span>
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <Code>{indicator}</Code>
          <EvidenceBadge kind={evidence_kind} />
        </div>
        <p className="text-xs text-zinc-400">{description}</p>
        {source_ref && (
          <p className="text-[11px] text-zinc-600 mt-1 font-mono truncate">{source_ref}</p>
        )}
      </div>
    </div>
  );
}

export default function TargetDetailPage() {
  const { id: projectId, target_id } = useParams<{ id: string; target_id: string }>();
  const [target, setTarget] = useState<TargetDetail | null>(null);
  const [evidence, setEvidence] = useState<TargetEvidenceRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [tRes, eRes] = await Promise.all([
          axios.get<TargetDetail>(`${API}/api/v1/projects/${projectId}/targets/${target_id}`),
          axios.get<TargetEvidenceRecord[]>(`${API}/api/v1/projects/${projectId}/targets/${target_id}/evidence`),
        ]);
        setTarget(tRes.data);
        setEvidence(eRes.data);
      } catch (err: unknown) {
        if (axios.isAxiosError(err)) setError(err.response?.data?.detail ?? err.message);
        else setError('Failed to load target');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [projectId, target_id]);

  if (loading) {
    return (
      <div className="p-6 max-w-5xl mx-auto animate-pulse space-y-4">
        <div className="h-8 bg-zinc-800/50 rounded w-64" />
        <div className="h-40 bg-zinc-800/50 rounded" />
        <div className="h-80 bg-zinc-800/50 rounded" />
      </div>
    );
  }

  if (error || !target) {
    return (
      <div className="p-6 max-w-5xl mx-auto">
        <div className="flex items-start gap-3 text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg p-5 text-sm">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error ?? 'Target not found'}</span>
        </div>
      </div>
    );
  }

  const totalScore = Math.min(
    (target.risk_reasons ?? []).reduce((s: number, r: { weight: number }) => s + r.weight, 0),
    10.0
  );

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Back */}
      <Link
        href={`/projects/${projectId}/targets`}
        className="inline-flex items-center gap-2 text-sm text-zinc-500 hover:text-zinc-300 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Targets
      </Link>

      {/* Hero */}
      <div className="bg-zinc-900/80 border border-zinc-800 rounded-lg p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="bg-zinc-800 p-3 rounded-lg">
              <Crosshair className="w-6 h-6 text-zinc-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold font-mono text-zinc-100">{target.name}</h1>
              <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                <Code>{target.module}</Code>
                {target.source_file && (
                  <span className="text-xs text-zinc-500 font-mono">
                    {target.source_file}{target.source_line ? `:${target.source_line}` : ''}
                    &nbsp;<EvidenceBadge kind="observed" />
                  </span>
                )}
              </div>
            </div>
          </div>
          <div className="text-right shrink-0">
            <div className="text-3xl font-bold font-mono text-zinc-100">{totalScore.toFixed(1)}</div>
            <div className="text-xs text-zinc-500 mt-0.5">/ 10 risk score</div>
            <Badge variant={riskVariant(totalScore)} >
              {totalScore >= 7.5 ? 'Critical' : totalScore >= 5 ? 'High' : totalScore >= 2.5 ? 'Medium' : 'Low'}
            </Badge>
          </div>
        </div>

        {/* Key facts grid */}
        <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4 border-t border-zinc-800 pt-5">
          {[
            { label: 'Input Type',      value: target.input_type },
            { label: 'Confidence',      value: `${(target.confidence * 100).toFixed(0)}%` },
            { label: 'Address',
              value: target.address
                ? `${target.address} (${target.address_kind ?? 'inferred'})`
                : 'Not available' },
            { label: 'Suggested Harness', value: HARNESS_LABELS[target.suggested_harness_type] ?? target.suggested_harness_type },
          ].map(({ label, value }) => (
            <div key={label}>
              <div className="text-xs text-zinc-500 uppercase tracking-wider mb-1">{label}</div>
              <div className="text-sm text-zinc-300 font-mono">{value}</div>
            </div>
          ))}
        </div>

        {/* Address epistemic warning */}
        {target.address && target.address_kind === 'inferred' && (
          <div className="mt-4 text-xs text-amber-400/80 bg-amber-500/10 border border-amber-500/20 rounded-md px-3 py-2">
            ⚠ The address above is <strong>inferred</strong> and has not been verified against a binary.
            Do not use it as a confirmed memory location.
          </div>
        )}
      </div>

      {/* Risk breakdown */}
      <Card>
        <CardHeader icon={Shield} title="Risk Breakdown" subtitle="Explainable scoring — each indicator shows its evidence kind" />
        <div className="px-5 py-2">
          {target.risk_reasons && target.risk_reasons.length > 0 ? (
            target.risk_reasons.map((r: {
              indicator: string;
              weight: number;
              description: string;
              evidence_kind: 'observed' | 'inferred' | 'user_provided';
              source_ref: string | null;
            }) => (
              <RiskBreakdownRow key={r.indicator} {...r} />
            ))
          ) : (
            <EmptyState icon={Shield} title="No scoring reasons" body="No indicators were found during analysis." />
          )}
        </div>
        <div className="px-5 py-3 border-t border-zinc-800 flex items-center justify-between">
          <span className="text-xs text-zinc-500">Evidence legend:</span>
          <div className="flex items-center gap-3">
            <EvidenceBadge kind="observed" />
            <EvidenceBadge kind="inferred" />
            <EvidenceBadge kind="user_provided" />
          </div>
        </div>
      </Card>

      {/* Attacker-controlled inputs */}
      {target.attacker_controlled_inputs && target.attacker_controlled_inputs.length > 0 && (
        <Card>
          <CardHeader icon={AlertCircle} title="Attacker-Controlled Inputs" subtitle="Parameters inferred to carry attacker data" />
          <div className="p-5 flex flex-wrap gap-2">
            {target.attacker_controlled_inputs.map((p: { name: string; type?: string }, i: number) => (
              <div key={i} className="bg-zinc-800 border border-zinc-700 rounded px-3 py-2">
                <span className="text-xs text-zinc-400 font-mono">{p.type ?? '?'}</span>
                <span className="text-xs text-zinc-200 font-mono font-semibold ml-2">{p.name}</span>
                <span className="ml-2"><EvidenceBadge kind="inferred" /></span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Memory operations */}
      {target.memory_operations && Object.keys(target.memory_operations).length > 0 && (
        <Card>
          <CardHeader icon={Code2} title="Memory Operations" subtitle="Observed memory-unsafe patterns in function body" />
          <div className="p-5 space-y-2">
            {Object.entries(target.memory_operations).map(([op, ref]) => (
              <div key={op} className="flex items-start gap-3 text-sm">
                <Code>{op}</Code>
                <span className="text-zinc-400 font-mono text-xs truncate">{String(ref)}</span>
                <EvidenceBadge kind="observed" />
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Call path */}
      <Card>
        <CardHeader icon={GitBranch} title="Call Path" subtitle="Reachability from known entry points" />
        {target.call_path && target.call_path.length > 0 ? (
          <div className="p-5 space-y-2 font-mono text-xs">
            {target.call_path.map((edge: { caller: string; callee: string; evidence_kind: string }, i: number) => (
              <div key={i} className="flex items-center gap-2 text-zinc-400">
                <Code>{edge.caller}</Code>
                <span className="text-zinc-600">→</span>
                <Code>{edge.callee}</Code>
                <EvidenceBadge kind={edge.evidence_kind as 'observed' | 'inferred' | 'user_provided'} />
              </div>
            ))}
          </div>
        ) : (
          <div className="px-5 py-4 text-sm text-zinc-500">
            Call-path analysis requires libclang or a pre-built call graph.
            Configure <Code>LIBCLANG_PATH</Code> in worker settings to enable this feature.
          </div>
        )}
      </Card>

      {/* Harness suggestion */}
      <Card>
        <CardHeader icon={FileCode} title="Suggested Harness Type" />
        <div className="p-5 text-sm text-zinc-400">
          Based on the indicators found, the recommended harness type is{' '}
          <strong className="text-zinc-200">{HARNESS_LABELS[target.suggested_harness_type] ?? target.suggested_harness_type}</strong>.
          Navigate to the <Link href={`/projects/${projectId}/harnesses`} className="text-blue-400 hover:underline">Harness Studio</Link> to generate a scaffold.
        </div>
      </Card>

      {/* Evidence ledger */}
      <Card>
        <CardHeader icon={BookOpen} title="Evidence Records" subtitle="Immutable SHA-256 hashed analysis records" />
        {evidence.length === 0 ? (
          <div className="px-5 py-4 text-sm text-zinc-500">No evidence records saved yet.</div>
        ) : (
          <div className="divide-y divide-zinc-800/60">
            {evidence.map(r => (
              <div key={r.id} className="px-5 py-3 text-xs font-mono">
                <div className="flex items-center justify-between">
                  <span className="text-zinc-400">{new Date(r.timestamp).toISOString()}</span>
                  <span className="text-zinc-600 truncate max-w-[240px]">{r.hash}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
