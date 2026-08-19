import { RecentActivity } from '@/types/models';
import { Terminal } from 'lucide-react';

interface RecentActivityPanelProps {
  activities: RecentActivity[];
}

export function RecentActivityPanel({ activities }: RecentActivityPanelProps) {
  return (
    <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-5 flex flex-col h-[400px]">
      <div className="flex items-center gap-2 mb-4">
        <Terminal className="w-4 h-4 text-zinc-400" />
        <h3 className="text-sm font-medium text-zinc-300">System Activity Log</h3>
      </div>
      
      <div className="flex-grow overflow-y-auto pr-2 space-y-1 font-mono text-xs">
        {!activities || activities.length === 0 ? (
          <div className="text-zinc-500 py-8 text-center italic">
            No activity recorded yet. System events will appear here once campaigns begin.
          </div>
        ) : (
          activities.map((activity) => (
            <div key={activity.id} className="flex items-start gap-3 py-1.5 border-b border-zinc-900 last:border-0 hover:bg-zinc-900/50 px-2 rounded">
              <span className="text-zinc-600 whitespace-nowrap shrink-0">
                [{new Date(activity.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}]
              </span>
              <span className="text-emerald-500/80 shrink-0 uppercase w-16">
                {activity.entity_type}
              </span>
              <span className="text-zinc-300 break-words">
                {activity.message}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
