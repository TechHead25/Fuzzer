"use client";

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ExecutionTrendPoint } from '@/types/models';
import { EmptyChart } from './EmptyChart';

interface ExecutionChartProps {
  data: ExecutionTrendPoint[];
}

export function ExecutionChart({ data }: ExecutionChartProps) {
  if (!data || data.length === 0) {
    return <EmptyChart title="Executions Over Time" />;
  }

  const formattedData = data.map(d => ({
    ...d,
    time: new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }));

  return (
    <div className="bg-zinc-900/80 border border-zinc-800 rounded-lg p-5 h-[350px] flex flex-col">
      <h3 className="text-sm font-medium text-zinc-300 mb-4">Executions Over Time</h3>
      <div className="flex-grow">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={formattedData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
            <defs>
              <linearGradient id="colorExecs" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
            <XAxis dataKey="time" stroke="#52525b" fontSize={12} tickLine={false} axisLine={false} />
            <YAxis stroke="#52525b" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => value >= 1000 ? `${(value / 1000).toFixed(1)}k` : value} />
            <Tooltip
              contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', color: '#e4e4e7', fontSize: '12px', borderRadius: '6px' }}
              itemStyle={{ color: '#e4e4e7' }}
            />
            <Area type="monotone" dataKey="executions" name="Total Executions" stroke="#f59e0b" strokeWidth={2} fillOpacity={1} fill="url(#colorExecs)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
