import Link from 'next/link';
import { Campaign } from '@/types/models';
import { Activity } from 'lucide-react';
import { twMerge } from 'tailwind-merge';

interface ActiveCampaignsTableProps {
  campaigns: Campaign[];
}

export function ActiveCampaignsTable({ campaigns }: ActiveCampaignsTableProps) {
  if (!campaigns || campaigns.length === 0) {
    return (
      <div className="bg-zinc-900/80 border border-zinc-800 rounded-lg p-5">
        <h3 className="text-sm font-medium text-zinc-300 mb-4">Active Campaigns</h3>
        <div className="text-sm text-zinc-500 py-8 text-center border border-dashed border-zinc-800 rounded-lg">
          No campaigns are currently running.
        </div>
      </div>
    );
  }

  return (
    <div className="bg-zinc-900/80 border border-zinc-800 rounded-lg overflow-hidden">
      <div className="p-5 border-b border-zinc-800 flex items-center justify-between">
        <h3 className="text-sm font-medium text-zinc-300 flex items-center gap-2">
          <Activity className="w-4 h-4 text-emerald-500" />
          Active Campaigns
        </h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-zinc-400 uppercase bg-zinc-950/50">
            <tr>
              <th className="px-5 py-3 font-medium">ID</th>
              <th className="px-5 py-3 font-medium">Fuzzer</th>
              <th className="px-5 py-3 font-medium">Status</th>
              <th className="px-5 py-3 font-medium text-right">Executions</th>
              <th className="px-5 py-3 font-medium text-right">Started</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/50">
            {campaigns.map((campaign) => (
              <tr key={campaign.id} className="hover:bg-zinc-800/30 transition-colors group">
                <td className="px-5 py-3 font-mono text-zinc-300">
                  <Link href={`/projects/${campaign.project_id}/campaigns/${campaign.id}`} className="hover:text-emerald-400">
                    #{campaign.id}
                  </Link>
                </td>
                <td className="px-5 py-3 text-zinc-200">
                  <div className="flex flex-col">
                    <span>{campaign.fuzzer}</span>
                    <span className="text-xs text-zinc-500">{campaign.instrumentation}</span>
                  </div>
                </td>
                <td className="px-5 py-3">
                  <span className={twMerge(
                    "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border",
                    campaign.status === 'running' ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" :
                    campaign.status === 'paused' ? "bg-amber-500/10 text-amber-400 border-amber-500/20" :
                    "bg-zinc-500/10 text-zinc-400 border-zinc-500/20"
                  )}>
                    {campaign.status}
                  </span>
                </td>
                <td className="px-5 py-3 text-right text-zinc-300 tabular-nums">
                  {campaign.executions.toLocaleString()}
                </td>
                <td className="px-5 py-3 text-right text-zinc-400">
                  {campaign.start_time ? new Date(campaign.start_time).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'N/A'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
