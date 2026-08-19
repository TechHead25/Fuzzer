"use client";

import Link from 'next/link';
import { ChevronUp, ChevronDown, ChevronsUpDown, ExternalLink } from 'lucide-react';
import { TargetSummary } from '@/types/discovery';
import { Badge, EvidenceBadge, Code, riskVariant } from './ui';

interface Props {
  targets: TargetSummary[];
  projectId: number;
  sortBy: string;
  sortDir: 'asc' | 'desc';
  onSort: (col: string) => void;
}

const STATUS_LABELS: Record<string, string> = {
  analyzed:   'Analyzed',
  pending:    'Pending',
  dismissed:  'Dismissed',
  harnessed:  'Harnessed',
};

function SortIcon({ col, sortBy, sortDir }: { col: string; sortBy: string; sortDir: string }) {
  if (col !== sortBy) return <ChevronsUpDown className="w-3 h-3 text-zinc-600" />;
  return sortDir === 'desc'
    ? <ChevronDown className="w-3 h-3 text-zinc-400" />
    : <ChevronUp className="w-3 h-3 text-zinc-400" />;
}

function RiskBar({ score }: { score: number }) {
  const pct = (score / 10) * 100;
  const color =
    score >= 7.5 ? 'bg-red-500'
    : score >= 5.0 ? 'bg-orange-500'
    : score >= 2.5 ? 'bg-yellow-500'
    : 'bg-blue-500';
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 bg-zinc-800 rounded-full h-1.5 overflow-hidden shrink-0">
        <div className={`h-1.5 rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono text-zinc-300">{score.toFixed(1)}</span>
    </div>
  );
}

export function TargetTable({ targets, projectId, sortBy, sortDir, onSort }: Props) {
  const cols: Array<{ key: string; label: string; sortable?: boolean }> = [
    { key: 'rank',       label: '#' },
    { key: 'name',       label: 'Function',       sortable: true },
    { key: 'module',     label: 'Module' },
    { key: 'risk_score', label: 'Risk',            sortable: true },
    { key: 'confidence', label: 'Confidence',      sortable: true },
    { key: 'input_type', label: 'Input' },
    { key: 'status',     label: 'Status' },
    { key: 'action',     label: '' },
  ];

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-zinc-800">
            {cols.map(col => (
              <th
                key={col.key}
                className={`px-4 py-3 text-left text-xs font-semibold text-zinc-500 uppercase tracking-wider whitespace-nowrap ${col.sortable ? 'cursor-pointer select-none hover:text-zinc-300' : ''}`}
                onClick={() => col.sortable && onSort(col.key)}
              >
                <span className="flex items-center gap-1">
                  {col.label}
                  {col.sortable && <SortIcon col={col.key} sortBy={sortBy} sortDir={sortDir} />}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-800/60">
          {targets.map((t, i) => (
            <tr key={t.id} className="hover:bg-zinc-800/30 transition-colors group">
              <td className="px-4 py-3 text-zinc-500 font-mono text-xs">{i + 1}</td>
              <td className="px-4 py-3">
                <div className="font-mono text-zinc-200 text-xs">{t.name}</div>
                {t.source_file && (
                  <div className="text-[11px] text-zinc-600 mt-0.5 truncate max-w-[220px]">
                    {t.source_file}{t.source_line ? `:${t.source_line}` : ''}
                  </div>
                )}
              </td>
              <td className="px-4 py-3">
                <Code>{t.module}</Code>
              </td>
              <td className="px-4 py-3">
                <div className="flex flex-col gap-1">
                  <Badge variant={riskVariant(t.risk_score)}>{t.risk_score.toFixed(1)}</Badge>
                  <RiskBar score={t.risk_score} />
                </div>
              </td>
              <td className="px-4 py-3">
                <span className="text-xs text-zinc-400 font-mono">
                  {(t.confidence * 100).toFixed(0)}%
                </span>
              </td>
              <td className="px-4 py-3">
                <span className="text-xs text-zinc-400">{t.input_type}</span>
              </td>
              <td className="px-4 py-3">
                <span className="text-xs text-zinc-400">{STATUS_LABELS[t.status] ?? t.status}</span>
              </td>
              <td className="px-4 py-3">
                <Link
                  href={`/projects/${projectId}/targets/${t.id}`}
                  className="opacity-0 group-hover:opacity-100 inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 transition-opacity"
                >
                  View <ExternalLink className="w-3 h-3" />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
