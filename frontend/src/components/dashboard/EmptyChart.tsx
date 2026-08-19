import { BarChart3 } from 'lucide-react';

interface EmptyChartProps {
  title: string;
  message?: string;
}

export function EmptyChart({ title, message }: EmptyChartProps) {
  return (
    <div className="bg-zinc-900/80 border border-zinc-800 rounded-lg p-5 h-full flex flex-col">
      <h3 className="text-sm font-medium text-zinc-300 mb-4">{title}</h3>
      <div className="flex flex-col items-center justify-center flex-grow py-12 text-center">
        <BarChart3 className="w-8 h-8 text-zinc-700 mb-3" />
        <p className="text-sm text-zinc-500">{message || 'No data available. Start a fuzzing campaign to see trends.'}</p>
      </div>
    </div>
  );
}
