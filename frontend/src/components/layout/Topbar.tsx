import { Bell } from 'lucide-react';

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
