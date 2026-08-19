import { Worker } from '@/types/models';
import { Server, Clock } from 'lucide-react';
import { twMerge } from 'tailwind-merge';

interface WorkerStatusPanelProps {
  workers: Worker[];
}

export function WorkerStatusPanel({ workers }: WorkerStatusPanelProps) {
  if (!workers || workers.length === 0) {
    return (
      <div className="bg-zinc-900/80 border border-zinc-800 rounded-lg p-5">
        <h3 className="text-sm font-medium text-zinc-300 mb-4">Worker Status</h3>
        <div className="text-sm text-zinc-500 py-8 text-center border border-dashed border-zinc-800 rounded-lg">
          No fuzz workers registered. Configure a Windows worker to begin fuzzing.
        </div>
      </div>
    );
  }

  return (
    <div className="bg-zinc-900/80 border border-zinc-800 rounded-lg p-5">
      <h3 className="text-sm font-medium text-zinc-300 mb-4">Worker Status</h3>
      <div className="space-y-3">
        {workers.map(worker => (
          <div key={worker.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-3 bg-zinc-800/50 rounded-lg border border-zinc-700/50">
            <div className="flex items-start sm:items-center gap-3 mb-2 sm:mb-0">
              <Server className="w-5 h-5 text-zinc-400 mt-0.5 sm:mt-0" />
              <div>
                <div className="text-sm font-medium text-zinc-200">{worker.hostname}</div>
                <div className="text-xs text-zinc-500">{worker.ip_address}</div>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1.5">
                <span className={twMerge(
                  "w-2 h-2 rounded-full",
                  worker.status === 'online' ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" :
                  worker.status === 'busy' ? "bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]" :
                  "bg-zinc-500"
                )} />
                <span className="text-xs text-zinc-300 capitalize">{worker.status}</span>
              </div>
              <div className="flex items-center gap-1.5 text-xs text-zinc-500">
                <Clock className="w-3.5 h-3.5" />
                <span>{worker.last_seen ? new Date(worker.last_seen).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Never'}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
