"use client";

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { CoverageTrendPoint } from '@/types/models';
import { EmptyChart } from './EmptyChart';

interface CoverageChartProps {
  data: CoverageTrendPoint[];
}

export function CoverageChart({ data }: CoverageChartProps) {
  if (!data || data.length === 0) {
    return <EmptyChart title="Coverage Trend" />;
  }

  const formattedData = data.map(d => ({
    ...d,
    time: new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }));

  return (
    <div className="bg-zinc-900/80 border border-zinc-800 rounded-lg p-5 h-[350px] flex flex-col">
      <h3 className="text-sm font-medium text-zinc-300 mb-4">Coverage Trend</h3>
      <div className="flex-grow">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={formattedData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
            <defs>
              <linearGradient id="colorEdges" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorBlocks" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
            <XAxis dataKey="time" stroke="#52525b" fontSize={12} tickLine={false} axisLine={false} />
            <YAxis stroke="#52525b" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value}`} />
            <Tooltip
              contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', color: '#e4e4e7', fontSize: '12px', borderRadius: '6px' }}
              itemStyle={{ color: '#e4e4e7' }}
            />
            <Area type="monotone" dataKey="edges" name="Edges" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#colorEdges)" />
            <Area type="monotone" dataKey="blocks" name="Blocks" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorBlocks)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
