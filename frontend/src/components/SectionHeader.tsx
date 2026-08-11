import React from 'react';
import { cn } from '../lib/utils';

interface SectionHeaderProps {
  title: string;
  color?: string; // CSS color or hex
  count?: number;
  className?: string;
  action?: React.ReactNode;
}

export const SectionHeader: React.FC<SectionHeaderProps> = ({
  title,
  color = '#2563EB',
  count,
  className,
  action
}) => {
  return (
    <div className={cn("flex items-center justify-between mb-3", className)}>
      <div className="flex items-center gap-2">
        <span
          className="w-2.5 h-2.5 rounded-full shrink-0 shadow-2xs"
          style={{ backgroundColor: color }}
        />
        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
          {title}
        </h3>
        {count !== undefined && (
          <span className="text-[11px] font-bold px-2 py-0.5 rounded-md bg-white border border-slate-200 text-slate-700 font-mono shadow-2xs">
            {count}
          </span>
        )}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
};
