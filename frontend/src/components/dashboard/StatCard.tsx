"use client";

import Link from 'next/link';
import { type LucideIcon } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: number | string;
  icon: LucideIcon;
  href?: string;
  format?: 'number' | 'speed' | 'percent';
}

export function StatCard({ label, value, icon: Icon, href, format = 'number' }: StatCardProps) {
  const formattedValue = (() => {
    if (typeof value === 'string') return value;
    switch (format) {
      case 'speed': return `${value.toLocaleString()} /s`;
      case 'percent': return `${value.toFixed(1)}%`;
      default: return value.toLocaleString();
    }
  })();

  const content = (
    <div className="bg-zinc-900/80 border border-zinc-800 rounded-lg p-5 hover:border-zinc-700 transition-colors h-full">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium text-zinc-400 uppercase tracking-wider">{label}</span>
        <Icon className="w-4 h-4 text-zinc-500" />
      </div>
      <div className="text-2xl font-bold text-zinc-100 tabular-nums">{formattedValue}</div>
    </div>
  );

  if (href) {
    return <Link href={href} className="block h-full">{content}</Link>;
  }
  return content;
}
