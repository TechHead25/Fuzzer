"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { TargetRiskItem } from '@/types/models';
import { EmptyChart } from './EmptyChart';

interface TargetRiskChartProps {
  data: TargetRiskItem[];
}

export function TargetRiskChart({ data }: TargetRiskChartProps) {
  if (!data || data.length === 0) {
    return <EmptyChart title="Target Risk Distribution" />;
  }

  const sortedData = [...data].sort((a, b) => b.risk_score - a.risk_score).slice(0, 10); // Top 10

  return (
    <div className="bg-zinc-900/80 border border-zinc-800 rounded-lg p-5 h-[350px] flex flex-col">
      <h3 className="text-sm font-medium text-zinc-300 mb-4">Target Risk Distribution</h3>
      <div className="flex-grow">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={sortedData} layout="vertical" margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" horizontal={false} />
            <XAxis type="number" stroke="#52525b" fontSize={12} tickLine={false} axisLine={false} domain={[0, 100]} />
            <YAxis type="category" dataKey="name" stroke="#52525b" fontSize={12} tickLine={false} axisLine={false} width={100} />
            <Tooltip
              contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', color: '#e4e4e7', fontSize: '12px', borderRadius: '6px' }}
              itemStyle={{ color: '#e4e4e7' }}
              cursor={{ fill: '#27272a', opacity: 0.4 }}
            />
            <Bar dataKey="risk_score" name="Risk Score" fill="#6366f1" radius={[0, 4, 4, 0]} barSize={20} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
