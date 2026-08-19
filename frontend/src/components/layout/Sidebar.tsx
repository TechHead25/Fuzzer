"use client";

import Link from 'next/link';
import { Home, Folder, Crosshair, FileCode, Database, Activity, ShieldAlert, FileText, Lock, BookOpen, Shield, Settings } from 'lucide-react';
import clsx from 'clsx';
import { usePathname } from 'next/navigation';

const mainNav = [
  { name: 'Dashboard', href: '/dashboard', icon: Home },
  { name: 'Projects', href: '/projects', icon: Folder },
];

const projectNav = [
  { name: 'Workspace', href: '/projects/1/workspace', icon: Crosshair },
  { name: 'Targets', href: '/projects/1/targets', icon: Crosshair },
  { name: 'Harnesses', href: '/projects/1/harnesses', icon: FileCode },
  { name: 'Corpus', href: '/projects/1/corpus', icon: Database },
  { name: 'Campaigns', href: '/projects/1/campaigns', icon: Activity },
];

const analysisNav = [
  { name: 'Crashes', href: '/projects/1/crashes', icon: ShieldAlert },
  { name: 'Findings', href: '/projects/1/findings', icon: Lock },
  { name: 'Evidence', href: '/projects/1/evidence', icon: BookOpen },
  { name: 'Coverage', href: '/projects/1/coverage', icon: Shield },
  { name: 'Reports', href: '/projects/1/reports', icon: FileText },
];

const systemNav = [
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  const renderNavGroup = (items: typeof mainNav) => (
    <ul className="space-y-1">
      {items.map((item) => {
        const isActive = pathname.startsWith(item.href) && (item.href !== '/projects' || pathname === '/projects');
        return (
          <li key={item.name}>
            <Link
              href={item.href}
              className={clsx(
                'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                isActive ? 'bg-zinc-800 text-zinc-100' : 'hover:bg-zinc-800/50 hover:text-zinc-100'
              )}
            >
              <item.icon className="w-4 h-4" />
              {item.name}
            </Link>
          </li>
        );
      })}
    </ul>
  );

  return (
    <div className="w-64 bg-zinc-950 border-r border-zinc-800 flex flex-col h-full text-zinc-300">
      <div className="h-16 flex items-center px-6 border-b border-zinc-800 text-zinc-100 font-bold text-lg tracking-wide">
        Fuzz-Sentinel
      </div>
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-6">
        <div>
          <div className="px-3 mb-2 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Overview</div>
          {renderNavGroup(mainNav)}
        </div>
        
        <div>
          <div className="px-3 mb-2 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Project Context</div>
          {renderNavGroup(projectNav)}
        </div>

        <div>
          <div className="px-3 mb-2 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Analysis</div>
          {renderNavGroup(analysisNav)}
        </div>

        <div className="border-t border-zinc-800/50 pt-4">
          {renderNavGroup(systemNav)}
        </div>
      </nav>
      <div className="p-4 border-t border-zinc-800">
        <div className="inline-flex items-center justify-center px-2 py-1 bg-zinc-900 border border-zinc-800 rounded text-xs font-mono text-zinc-500">
          v0.1 MVP
        </div>
      </div>
    </div>
  );
}
