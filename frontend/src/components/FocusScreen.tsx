import React, { useState } from 'react';
import { motion } from 'motion/react';
import { Signal } from '../lib/data';
import { SignalCard } from './SignalCard';
import { CheckCircle2, Flame, Zap, Calendar, Clock, CheckCircle, Ghost } from 'lucide-react';
import { cn } from '../lib/utils';

interface FocusScreenProps {
  signals: Signal[];
  onMoveBucket: (id: string, newBucket: Signal['bucket']) => void;
  onAction: (id: string, actionName: string) => void;
  onOpenDetail: (signal: Signal) => void;
}

export const FocusScreen: React.FC<FocusScreenProps> = ({
  signals,
  onMoveBucket,
  onAction,
  onOpenDetail
}) => {
  const [activeBucket, setActiveBucket] = useState<Signal['bucket']>('do-now');

  const buckets: { key: Signal['bucket']; label: string; icon: React.ReactNode; color: string }[] = [
    { key: 'do-now', label: 'Do now', icon: <Flame className="w-3.5 h-3.5 text-rose-600" />, color: '#E11D48' },
    { key: 'today', label: 'Today', icon: <Zap className="w-3.5 h-3.5 text-amber-600" />, color: '#D97706' },
    { key: 'this-week', label: 'This week', icon: <Calendar className="w-3.5 h-3.5 text-blue-600" />, color: '#2563EB' },
    { key: 'waiting', label: 'Waiting', icon: <Clock className="w-3.5 h-3.5 text-slate-500" />, color: '#64748B' },
    { key: 'completed', label: 'Completed', icon: <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />, color: '#059669' },
    { key: 'ignored', label: 'Ignored', icon: <Ghost className="w-3.5 h-3.5 text-slate-400" />, color: '#94A3B8' },
  ];

  const filteredSignals = signals.filter((s) => s.bucket === activeBucket);

  const getBorderColorClass = (bucket: Signal['bucket']) => {
    switch (bucket) {
      case 'do-now': return 'border-l-4 border-l-rose-600';
      case 'today': return 'border-l-4 border-l-amber-500';
      case 'this-week': return 'border-l-4 border-l-blue-600';
      case 'waiting': return 'border-l-4 border-l-slate-400';
      case 'completed': return 'border-l-4 border-l-emerald-500';
      case 'ignored': return 'border-l-4 border-l-slate-300';
      default: return '';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">
          Focus Buckets
        </h1>
        <p className="text-sm text-slate-600 mt-0.5 font-medium">
          Human-readable priority groups categorized automatically by AI.
        </p>
      </div>

      {/* Bucket Filter Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 no-scrollbar">
        {buckets.map((b) => {
          const count = signals.filter((s) => s.bucket === b.key).length;
          const isActive = activeBucket === b.key;

          return (
            <button
              key={b.key}
              onClick={() => setActiveBucket(b.key)}
              className={cn(
                "flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap cursor-pointer shrink-0 border",
                isActive
                  ? "bg-slate-900 text-white border-slate-900 shadow-sm"
                  : "bg-white border-slate-200 text-slate-700 hover:bg-slate-50 hover:text-slate-900 shadow-2xs"
              )}
            >
              {b.icon}
              <span>{b.label}</span>
              <span
                className={cn(
                  "px-1.5 py-0.2 rounded-full text-[10px] font-mono font-bold",
                  isActive ? "bg-slate-800 text-blue-400" : "bg-slate-100 text-slate-600"
                )}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Signal List for Active Bucket */}
      <div className="space-y-3">
        {filteredSignals.length > 0 ? (
          filteredSignals.map((signal) => (
            <div key={signal.id} className={cn("rounded-xl overflow-hidden shadow-2xs", getBorderColorClass(signal.bucket))}>
              <SignalCard
                signal={signal}
                onMoveBucket={onMoveBucket}
                onAction={onAction}
                onOpenDetail={onOpenDetail}
              />
            </div>
          ))
        ) : (
          <div className="rounded-2xl bg-white border border-dashed border-slate-300 p-12 text-center flex flex-col items-center justify-center shadow-2xs">
            <CheckCircle2 className="w-12 h-12 text-slate-300 mb-3" />
            <h3 className="text-sm font-bold text-slate-800 mb-1">
              Nothing in this bucket.
            </h3>
            <p className="text-xs text-slate-500 max-w-sm font-medium">
              Signal has automatically organized or cleared all items in this bucket.
            </p>
          </div>
        )}
      </div>
    </motion.div>
  );
};
