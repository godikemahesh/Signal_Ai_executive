import React, { useState } from 'react';
import {
  Briefcase,
  CreditCard,
  Package,
  MessageCircle,
  GitBranch,
  Newspaper,
  Tag,
  ExternalLink,
  ChevronDown,
  Clock,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { motion } from 'motion/react';
import { Signal } from '../lib/data';
import { cn } from '../lib/utils';
import { BucketBadge } from './BucketBadge';

interface SignalCardProps {
  signal: Signal;
  variant?: 'default' | 'compact' | 'timeline';
  onMoveBucket?: (id: string, newBucket: Signal['bucket']) => void;
  onAction?: (id: string, actionName: string) => void;
  onOpenDetail?: (signal: Signal) => void;
  primaryButtonText?: string;
  secondaryButtonText?: string;
}

export const SignalCard: React.FC<SignalCardProps> = ({
  signal,
  variant = 'default',
  onMoveBucket,
  onAction,
  onOpenDetail,
  primaryButtonText,
  secondaryButtonText
}) => {
  const [showBucketMenu, setShowBucketMenu] = useState(false);
  const [isCompleted, setIsCompleted] = useState(signal.bucket === 'completed');

  const getCategoryIcon = (category: Signal['category']) => {
    const iconClass = "w-5 h-5 text-blue-600";
    switch (category) {
      case 'interview': return <Briefcase className={iconClass} />;
      case 'finance': return <CreditCard className="w-5 h-5 text-amber-600" />;
      case 'shopping': return <Package className="w-5 h-5 text-blue-600" />;
      case 'personal': return <MessageCircle className="w-5 h-5 text-emerald-600" />;
      case 'github': return <GitBranch className="w-5 h-5 text-purple-600" />;
      case 'newsletter': return <Newspaper className="w-5 h-5 text-slate-500" />;
      case 'marketing': return <Tag className="w-5 h-5 text-pink-600" />;
      default: return <MessageCircle className={iconClass} />;
    }
  };

  const handlePrimaryClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    const actionName = primaryButtonText || getActionLabel(signal.actionType).primary;
    if (onAction) {
      onAction(signal.id, actionName);
    } else {
      alert(`Executed action: "${actionName}" for ${signal.subject}`);
    }
  };

  const handleSecondaryClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    const actionName = secondaryButtonText || getActionLabel(signal.actionType).secondary;
    if (onAction) {
      onAction(signal.id, actionName);
    } else {
      alert(`Executed action: "${actionName}" for ${signal.subject}`);
    }
  };

  const getActionLabel = (actionType: Signal['actionType']) => {
    switch (actionType) {
      case 'reply':
        return { primary: 'Reply now', secondary: 'Suggest slots' };
      case 'complete':
        return { primary: 'Start now', secondary: 'Snooze 1h' };
      case 'pay':
        return { primary: 'Pay now', secondary: 'Remind tonight' };
      case 'upload':
        return { primary: 'Upload docs', secondary: 'Snooze 1d' };
      case 'review':
        return { primary: 'Review PR', secondary: 'Dismiss' };
      default:
        return { primary: 'View details', secondary: 'Archive' };
    }
  };

  const actionLabels = getActionLabel(signal.actionType);
  const primaryText = primaryButtonText || actionLabels.primary;
  const secondaryText = secondaryButtonText || actionLabels.secondary;

  const buckets: Signal['bucket'][] = ['do-now', 'today', 'this-week', 'waiting', 'completed', 'ignored'];

  return (
    <motion.div
      whileHover={{ y: -1 }}
      transition={{ duration: 0.2 }}
      onClick={() => onOpenDetail && onOpenDetail(signal)}
      className={cn(
        "group relative rounded-xl bg-white border border-slate-200/90 p-5 shadow-sm hover:border-slate-300 hover:shadow-md transition-all cursor-pointer",
        variant === 'compact' && "p-3.5",
        isCompleted && "opacity-75 bg-slate-50/80 border-slate-200"
      )}
    >
      {/* Top Row: Category Icon + Entity Name + Status Badge */}
      <div className="flex items-center justify-between gap-3 mb-2.5">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="p-1.5 rounded-lg bg-slate-100 border border-slate-200/80 shrink-0">
            {getCategoryIcon(signal.category)}
          </div>
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-tight truncate">
            {signal.entityName}
          </span>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {signal.status === 'new' && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200">
              <span className="w-1.5 h-1.5 rounded-full bg-rose-600 animate-pulse" />
              New
            </span>
          )}
          {signal.status === 'changed' && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-600" />
              Updated
            </span>
          )}

          {/* Bucket dropdown / picker */}
          {onMoveBucket && (
            <div className="relative" onClick={(e) => e.stopPropagation()}>
              <button
                onClick={() => setShowBucketMenu(!showBucketMenu)}
                className="flex items-center gap-1 px-2 py-0.5 rounded-md text-xs bg-slate-50 border border-slate-200 text-slate-600 hover:border-slate-300 hover:text-slate-900 transition-colors"
                title="Move to bucket"
              >
                <BucketBadge bucket={signal.bucket} showIcon={true} />
                <ChevronDown className="w-3 h-3 text-slate-400" />
              </button>

              {showBucketMenu && (
                <div className="absolute right-0 mt-1 w-38 rounded-xl bg-white border border-slate-200 shadow-xl z-30 py-1">
                  <div className="px-3 py-1 text-[10px] font-bold uppercase text-slate-400 border-b border-slate-100">
                    Move to bucket
                  </div>
                  {buckets.map((b) => (
                    <button
                      key={b}
                      onClick={() => {
                        onMoveBucket(signal.id, b);
                        setShowBucketMenu(false);
                      }}
                      className={cn(
                        "w-full text-left px-3 py-1.5 text-xs hover:bg-slate-50 flex items-center justify-between transition-colors font-medium",
                        signal.bucket === b ? "text-blue-600 font-bold" : "text-slate-600"
                      )}
                    >
                      <BucketBadge bucket={b} />
                      {signal.bucket === b && <span className="text-[10px]">✓</span>}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Subject Line */}
      <h4 className="text-[15px] font-bold text-slate-900 mb-1.5 line-clamp-1 group-hover:text-blue-600 transition-colors">
        {signal.subject}
      </h4>

      {/* Preview snippet */}
      <p className="text-sm text-slate-600 leading-relaxed line-clamp-2 mb-3.5">
        {signal.preview}
      </p>

      {/* Deadline / Context Banner if exists */}
      {signal.deadlineText && (
        <div className="flex items-center gap-1.5 text-xs font-bold text-rose-700 mb-3.5 bg-rose-50 px-2.5 py-1 rounded-lg border border-rose-200/80 w-fit">
          <Clock className="w-3.5 h-3.5 shrink-0" />
          <span>{signal.deadlineText}</span>
        </div>
      )}

      {/* Bottom Row: Actions & Open in Gmail link */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-2.5 border-t border-slate-100">
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            if (onAction) onAction(signal.id, 'Open in Gmail');
            else if (signal.gmailUrl) window.open(signal.gmailUrl, '_blank');
          }}
          className="inline-flex items-center gap-1 text-xs font-semibold text-slate-500 hover:text-blue-600 transition-colors py-1 cursor-pointer bg-transparent border-0 p-0"
        >
          <span>Open in Gmail</span>
          <ExternalLink className="w-3 h-3" />
        </button>

        <div className="flex items-center gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              if (onAction) onAction(signal.id, 'Mark Handled');
            }}
            className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 hover:bg-emerald-100 transition-all cursor-pointer shadow-2xs"
            title="Mark as completed locally in Signal without launching Gmail"
          >
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Mark Handled</span>
          </button>

          {signal.actionType !== 'no-action' && (
            <>
              <button
                onClick={handleSecondaryClick}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-700 border border-slate-200 bg-white hover:bg-slate-50 transition-all cursor-pointer shadow-2xs"
              >
                {secondaryText}
              </button>
              <button
                onClick={handlePrimaryClick}
                className="px-3.5 py-1.5 rounded-lg text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 shadow-sm transition-all cursor-pointer"
              >
                {primaryText}
              </button>
            </>
          )}
        </div>
      </div>
    </motion.div>
  );
};
