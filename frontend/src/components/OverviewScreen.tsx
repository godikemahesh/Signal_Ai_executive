import React from 'react';
import { motion } from 'motion/react';
import { Signal } from '../lib/data';
import { SectionHeader } from './SectionHeader';
import { SignalCard } from './SignalCard';
import { CheckCircle } from 'lucide-react';

interface OverviewScreenProps {
  signals: Signal[];
  overviewData?: any;
  onMoveBucket: (id: string, newBucket: Signal['bucket']) => void;
  onAction: (id: string, actionName: string) => void;
  onOpenDetail: (signal: Signal) => void;
}

export const OverviewScreen: React.FC<OverviewScreenProps> = ({
  signals,
  overviewData,
  onMoveBucket,
  onAction,
  onOpenDetail
}) => {
  // Filter needs_action signals strictly excluding completed/ignored items
  const rawNeedsAction = overviewData?.needs_action?.length
    ? overviewData.needs_action
    : signals.filter((s) => s.bucket === 'do-now' || s.bucket === 'today');

  const needsActionSignals = rawNeedsAction.filter(
    (s: Signal) => s.bucket !== 'completed' && s.bucket !== 'ignored'
  );

  const changedSignals = overviewData?.changed?.length
    ? overviewData.changed
    : signals.filter((s) => s.status === 'changed' || s.bucket === 'today');

  const dueSoonSignals = overviewData?.due_soon?.length
    ? overviewData.due_soon
    : signals.filter((s) => s.deadlineText || s.deadline || s.actionType === 'pay');

  const greeting = overviewData?.greeting || 'hey there.';
  const summary = overviewData?.summary || (needsActionSignals.length > 0 ? `Since your last visit, ${needsActionSignals.length} item(s) require executive decision.` : 'All caught up! Zero urgent actions remaining.');
  const handled = overviewData?.handled_automatically || {
    newsletters_summarized: 0,
    marketing_archived: 0,
    github_notifications: 0,
    promotions_archived: 0
  };

  const getDotColorClass = (color?: string) => {
    switch (color) {
      case 'emerald': return 'bg-emerald-500';
      case 'blue': return 'bg-blue-500';
      case 'amber': return 'bg-amber-500';
      case 'purple': return 'bg-purple-500';
      case 'indigo': return 'bg-indigo-500';
      case 'rose': return 'bg-rose-500';
      case 'cyan': return 'bg-cyan-500';
      case 'teal': return 'bg-teal-500';
      default: return 'bg-slate-400';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.3 }}
      className="space-y-8"
    >
      {/* Hero Section */}
      <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-sm flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              {greeting}
            </h1>
            <span className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs font-bold rounded-md border border-blue-100 uppercase tracking-wider">
              Executive View
            </span>
          </div>
          <p className="text-sm text-slate-600 font-medium">
            {summary}
          </p>
        </div>
      </div>

      {/* Section: 🔥 Needs Action */}
      <div>
        <SectionHeader
          title="Needs action"
          color="#E11D48"
          count={needsActionSignals.length}
        />
        <div className="space-y-3">
          {needsActionSignals.length === 0 ? (
            <p className="text-xs text-slate-400 font-medium italic p-3 bg-white rounded-xl border border-slate-200/70">
              No immediate action items. Your inbox focus is clear!
            </p>
          ) : (
            needsActionSignals.map((signal: Signal) => (
              <SignalCard
                key={signal.id}
                signal={signal}
                onMoveBucket={onMoveBucket}
                onAction={onAction}
                onOpenDetail={onOpenDetail}
              />
            ))
          )}
        </div>
      </div>

      {/* Section: ⚡ Changed */}
      {changedSignals.length > 0 && (
        <div>
          <SectionHeader
            title="Changed since you last checked"
            color="#2563EB"
            count={changedSignals.length}
          />
          <div className="space-y-3">
            {changedSignals.map((signal: Signal) => (
              <SignalCard
                key={signal.id}
                signal={signal}
                onMoveBucket={onMoveBucket}
                onAction={onAction}
                onOpenDetail={onOpenDetail}
              />
            ))}
          </div>
        </div>
      )}

      {/* Section: 💳 Due Soon */}
      {dueSoonSignals.length > 0 && (
        <div>
          <SectionHeader
            title="Due soon"
            color="#D97706"
            count={dueSoonSignals.length}
          />
          <div className="space-y-3">
            {dueSoonSignals.map((signal: Signal) => (
              <SignalCard
                key={signal.id}
                signal={signal}
                onMoveBucket={onMoveBucket}
                onAction={onAction}
                onOpenDetail={onOpenDetail}
              />
            ))}
          </div>
        </div>
      )}

      {/* Section: 📥 Handled Automatically */}
      <div>
        <SectionHeader
          title="Handled automatically"
          color="#64748B"
        />
        <div className="rounded-xl bg-white border border-slate-200/90 shadow-sm p-5 space-y-3">
          {handled.dynamic_categories && handled.dynamic_categories.length > 0 ? (
            handled.dynamic_categories.map((cat: any, idx: number) => (
              <div key={cat.category_key || idx} className="flex items-center justify-between text-sm text-slate-700 hover:text-slate-900 transition-colors py-0.5">
                <span className="flex items-center gap-2.5 font-medium">
                  <span className={`w-2 h-2 rounded-full shrink-0 ${getDotColorClass(cat.color)}`} />
                  {cat.count} {cat.label}
                </span>
                <span className="text-xs text-slate-500 font-mono font-semibold">{cat.action_text}</span>
              </div>
            ))
          ) : (
            <>
              <div className="flex items-center justify-between text-sm text-slate-700 hover:text-slate-900 transition-colors py-0.5">
                <span className="flex items-center gap-2.5 font-medium">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0" />
                  {handled.newsletters_summarized || 0} newsletters summarized
                </span>
                <span className="text-xs text-slate-500 font-mono font-semibold">→ Auto-read</span>
              </div>

              <div className="flex items-center justify-between text-sm text-slate-700 hover:text-slate-900 transition-colors py-0.5">
                <span className="flex items-center gap-2.5 font-medium">
                  <span className="w-2 h-2 rounded-full bg-slate-400 shrink-0" />
                  {handled.marketing_archived || 0} marketing emails archived
                </span>
                <span className="text-xs text-slate-500 font-semibold">Auto-filtered</span>
              </div>

              <div className="flex items-center justify-between text-sm text-slate-700 hover:text-slate-900 transition-colors py-0.5">
                <span className="flex items-center gap-2.5 font-medium">
                  <span className="w-2 h-2 rounded-full bg-blue-500 shrink-0" />
                  {handled.github_notifications || 0} GitHub notifications
                </span>
                <span className="text-xs text-slate-500 font-semibold">Non-blocking</span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Calming Footer */}
      <div className="mt-8 p-4 rounded-xl bg-slate-100/90 border border-slate-200 text-center shadow-2xs">
        <div className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600">
          <CheckCircle className="w-4 h-4 text-emerald-600" />
          <span>Nothing else needs your attention. All systems clear.</span>
        </div>
      </div>
    </motion.div>
  );
};

