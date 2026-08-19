"use client";

import { type LucideIcon } from 'lucide-react';
import Link from 'next/link';
import { clsx } from 'clsx';

type BadgeVariant = 'critical' | 'high' | 'medium' | 'low' | 'info' | 'observed' | 'inferred' | 'user_provided';

const BADGE_STYLES: Record<BadgeVariant, string> = {
  critical:      'bg-red-500/15 text-red-400 border-red-500/30',
  high:          'bg-orange-500/15 text-orange-400 border-orange-500/30',
  medium:        'bg-yellow-500/15 text-yellow-400 border-yellow-500/30',
  low:           'bg-blue-500/15 text-blue-400 border-blue-500/30',
  info:          'bg-zinc-700/50 text-zinc-400 border-zinc-600/50',
  observed:      'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  inferred:      'bg-sky-500/15 text-sky-400 border-sky-500/30',
  user_provided: 'bg-violet-500/15 text-violet-400 border-violet-500/30',
};

export function Badge({ variant, children }: { variant: BadgeVariant; children: React.ReactNode }) {
  return (
    <span className={clsx(
      'inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium border',
      BADGE_STYLES[variant]
    )}>
      {children}
    </span>
  );
}

/** Convert a 0–10 risk score to a badge variant */
export function riskVariant(score: number): BadgeVariant {
  if (score >= 7.5) return 'critical';
  if (score >= 5.0) return 'high';
  if (score >= 2.5) return 'medium';
  return 'low';
}

/** Evidence kind badge */
export function EvidenceBadge({ kind }: { kind: 'observed' | 'inferred' | 'user_provided' }) {
  const labels: Record<string, string> = {
    observed: 'Observed',
    inferred: 'Inferred',
    user_provided: 'User-Provided',
  };
  return <Badge variant={kind}>{labels[kind] ?? kind}</Badge>;
}

/** A monospace inline code snippet */
export function Code({ children }: { children: React.ReactNode }) {
  return (
    <code className="px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-300 text-xs font-mono">
      {children}
    </code>
  );
}

/** Progress bar */
export function ProgressBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div className="w-full bg-zinc-800 rounded-full h-2 overflow-hidden">
      <div
        className="h-2 rounded-full bg-blue-500 transition-all duration-300"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

/** Section card wrapper */
export function Card({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={clsx('bg-zinc-900/80 border border-zinc-800 rounded-lg', className)}>
      {children}
    </div>
  );
}

/** Section heading inside a card */
export function CardHeader({ icon: Icon, title, subtitle }: {
  icon?: LucideIcon;
  title: string;
  subtitle?: string;
}) {
  return (
    <div className="flex items-center gap-3 px-5 py-4 border-b border-zinc-800">
      {Icon && <Icon className="w-4 h-4 text-zinc-400 shrink-0" />}
      <div>
        <h2 className="text-sm font-semibold text-zinc-200">{title}</h2>
        {subtitle && <p className="text-xs text-zinc-500 mt-0.5">{subtitle}</p>}
      </div>
    </div>
  );
}

/** Empty state panel */
export function EmptyState({ icon: Icon, title, body, action }: {
  icon: LucideIcon;
  title: string;
  body: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center px-6">
      <div className="bg-zinc-900 p-4 rounded-full mb-4 ring-1 ring-zinc-800">
        <Icon className="w-7 h-7 text-zinc-600" />
      </div>
      <h3 className="text-base font-semibold text-zinc-300 mb-2">{title}</h3>
      <p className="text-sm text-zinc-500 max-w-sm">{body}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
