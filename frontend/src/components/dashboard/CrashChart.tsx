"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { CrashTrendPoint } from '@/types/models';
import { EmptyChart } from './EmptyChart';

interface CrashChartProps {
  data: CrashTrendPoint[];
}

export function CrashChart({ data }: CrashChartProps) {
  if (!data || data.length === 0) {
    return <EmptyChart title="Crash Discovery Timeline" />;
  }

  const formattedData = data.map(d => ({
    ...d,
    time: new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }));

  return (
    <div className="bg-zinc-900/80 border border-zinc-800 rounded-lg p-5 h-[350px] flex flex-col">
      <h3 className="text-sm font-medium text-zinc-300 mb-4">Crash Discovery Timeline</h3>
      <div className="flex-grow">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={formattedData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
            <XAxis dataKey="time" stroke="#52525b" fontSize={12} tickLine={false} axisLine={false} />
            <YAxis stroke="#52525b" fontSize={12} tickLine={false} axisLine={false} />
            <Tooltip
              contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', color: '#e4e4e7', fontSize: '12px', borderRadius: '6px' }}
              itemStyle={{ color: '#e4e4e7' }}
              cursor={{ fill: '#27272a', opacity: 0.4 }}
            />
            <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', color: '#a1a1aa' }} />
            <Bar dataKey="total_crashes" name="Total Crashes" fill="#ef4444" radius={[4, 4, 0, 0]} />
            <Bar dataKey="unique_crashes" name="Unique Crashes" fill="#f97316" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
