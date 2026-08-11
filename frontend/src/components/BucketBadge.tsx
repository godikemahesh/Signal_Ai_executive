import React from 'react';
import { cn } from '../lib/utils';

interface BucketBadgeProps {
  bucket: string;
  className?: string;
  showIcon?: boolean;
}

export const BucketBadge: React.FC<BucketBadgeProps> = ({ bucket, className, showIcon = true }) => {
  let colorClass = 'text-slate-600 bg-slate-100 border-slate-200';
  let label = bucket;
  let icon = '';

  switch (bucket) {
    case 'do-now':
      colorClass = 'text-rose-700 bg-rose-50 border-rose-200 font-bold';
      label = 'Do now';
      icon = '🔥';
      break;
    case 'today':
      colorClass = 'text-amber-700 bg-amber-50 border-amber-200 font-semibold';
      label = 'Today';
      icon = '⚡';
      break;
    case 'this-week':
      colorClass = 'text-blue-700 bg-blue-50 border-blue-200 font-semibold';
      label = 'This week';
      icon = '📅';
      break;
    case 'waiting':
      colorClass = 'text-slate-600 bg-slate-100 border-slate-200 font-medium';
      label = 'Waiting';
      icon = '⏳';
      break;
    case 'completed':
      colorClass = 'text-emerald-700 bg-emerald-50 border-emerald-200 font-semibold';
      label = 'Completed';
      icon = '✓';
      break;
    case 'ignored':
      colorClass = 'text-slate-500 bg-slate-100 border-slate-200 font-normal';
      label = 'Ignored';
      icon = '👻';
      break;
    default:
      label = bucket;
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-xs border transition-colors',
        colorClass,
        className
      )}
    >
      {showIcon && icon && <span className="text-[11px]">{icon}</span>}
      <span>{label}</span>
    </span>
  );
};
