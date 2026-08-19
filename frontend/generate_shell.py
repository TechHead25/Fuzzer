import os
from pathlib import Path

base = Path("src")

(base / "lib").mkdir(parents=True, exist_ok=True)
(base / "types").mkdir(parents=True, exist_ok=True)
(base / "components" / "layout").mkdir(parents=True, exist_ok=True)

# 1. API Client
api_ts = """import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;
"""
(base / "lib" / "api.ts").write_text(api_ts)

# 2. Types
models_ts = """export interface Project {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
}

export interface Target {
  id: number;
  name: string;
  module: string;
  risk_score: number;
  status: string;
}
"""
(base / "types" / "models.ts").write_text(models_ts)

# 3. Sidebar
sidebar_tsx = """import Link from 'next/link';
import { Home, Folder, Crosshair, FileCode, Database, Activity, ShieldAlert, FileText, Lock } from 'lucide-react';
import clsx from 'clsx';
import { usePathname } from 'next/navigation';

const navItems = [
  { name: 'Dashboard', href: '/dashboard', icon: Home },
  { name: 'Projects', href: '/projects', icon: Folder },
  { name: 'Targets', href: '/projects/1/targets', icon: Crosshair },
  { name: 'Harnesses', href: '/projects/1/harnesses', icon: FileCode },
  { name: 'Corpus', href: '/projects/1/corpus', icon: Database },
  { name: 'Campaigns', href: '/projects/1/campaigns', icon: Activity },
  { name: 'Crashes', href: '/projects/1/crashes', icon: ShieldAlert },
  { name: 'Findings', href: '/projects/1/findings', icon: Lock },
  { name: 'Reports', href: '/projects/1/reports', icon: FileText },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <div className="w-64 bg-zinc-950 border-r border-zinc-800 flex flex-col h-full text-zinc-300">
      <div className="h-16 flex items-center px-6 border-b border-zinc-800 text-zinc-100 font-bold text-lg tracking-wide">
        Fuzz-Sentinel
      </div>
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.href) && (item.href !== '/projects' || pathname === '/projects');
          return (
            <Link
              key={item.name}
              href={item.href}
              className={clsx(
                'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                isActive ? 'bg-zinc-800 text-zinc-100' : 'hover:bg-zinc-800/50 hover:text-zinc-100'
              )}
            >
              <item.icon className="w-4 h-4" />
              {item.name}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
"""
(base / "components" / "layout" / "Sidebar.tsx").write_text(sidebar_tsx)

# 4. Topbar
topbar_tsx = """import { Bell } from 'lucide-react';

export function Topbar() {
  return (
    <header className="h-16 bg-zinc-950 border-b border-zinc-800 flex items-center justify-between px-6 shrink-0">
      <div className="flex items-center gap-4">
        {/* Project Selector Placeholder */}
        <div className="text-sm font-medium bg-zinc-900 border border-zinc-800 rounded-md px-3 py-1.5 text-zinc-300">
          Global View
        </div>
      </div>
      <div className="flex items-center gap-4">
        <button className="text-zinc-400 hover:text-zinc-100 transition-colors">
          <Bell className="w-5 h-5" />
        </button>
      </div>
    </header>
  );
}
"""
(base / "components" / "layout" / "Topbar.tsx").write_text(topbar_tsx)

# 5. AppShell Layout
layout_tsx = """import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Fuzz-Sentinel",
  description: "Intelligent continuous fuzzing and security-assurance platform.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-zinc-950 text-zinc-100 h-screen overflow-hidden flex`}>
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <Topbar />
          <main className="flex-1 overflow-auto bg-zinc-950">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
"""
(base / "app" / "layout.tsx").write_text(layout_tsx)

# 6. Dashboard Page (Empty State)
dashboard_tsx = """import { ShieldAlert } from 'lucide-react';

export default function Dashboard() {
  return (
    <div className="p-8 h-full flex flex-col">
      <h1 className="text-2xl font-bold mb-6 text-zinc-100">Dashboard</h1>
      
      <div className="flex-1 flex flex-col items-center justify-center text-center border-2 border-dashed border-zinc-800 rounded-lg p-12 bg-zinc-900/30">
        <div className="bg-zinc-900 p-4 rounded-full mb-4 ring-1 ring-zinc-800">
          <ShieldAlert className="w-8 h-8 text-zinc-500" />
        </div>
        <h2 className="text-xl font-semibold text-zinc-200 mb-2">No Campaigns Running</h2>
        <p className="text-zinc-400 max-w-md mb-6">
          There are no real campaigns or results available yet. Start by discovering targets and creating a fuzzing harness for SumatraPDF.
        </p>
        <button className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors">
          Initialize Project
        </button>
      </div>
    </div>
  );
}
"""
(base / "app" / "dashboard" / "page.tsx").write_text(dashboard_tsx)

print("Frontend shell generated.")
