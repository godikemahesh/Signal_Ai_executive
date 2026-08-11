import React from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Signal } from '../lib/data';
import { X, ExternalLink, Clock, ShieldAlert, Sparkles, CheckCircle2, ArrowRight } from 'lucide-react';
import { BucketBadge } from './BucketBadge';

interface SignalDetailModalProps {
  signal: Signal | null;
  onClose: () => void;
  onMoveBucket: (id: string, newBucket: Signal['bucket']) => void;
  onAction: (id: string, actionName: string) => void;
}

export const SignalDetailModal: React.FC<SignalDetailModalProps> = ({
  signal,
  onClose,
  onMoveBucket,
  onAction
}) => {
  if (!signal) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          transition={{ duration: 0.2 }}
          className="relative w-full max-w-xl rounded-2xl bg-white border border-slate-200 p-6 shadow-2xl space-y-5 max-h-[90vh] overflow-y-auto"
        >
          {/* Close Button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>

          {/* Modal Header */}
          <div className="pr-8 space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-tight">
                {signal.entityName}
              </span>
              <BucketBadge bucket={signal.bucket} />
            </div>

            <h2 className="text-lg font-bold text-slate-900 leading-snug">
              {signal.subject}
            </h2>
          </div>

          {/* AI Intelligence Assessment */}
          <div className="rounded-xl bg-blue-50/70 border border-blue-100 p-4 space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-blue-700 uppercase tracking-wider">
              <Sparkles className="w-4 h-4 text-blue-600" />
              <span>AI Signal Analysis</span>
            </div>
            <p className="text-xs text-slate-700 leading-relaxed font-medium">
              Signal analyzed this thread and extracted an active prompt/deadline. Priority bucketed as <strong className="text-slate-900">{signal.bucket}</strong>.
            </p>
          </div>

          {/* Full Preview Text */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
              Email Context
            </h4>
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-sm text-slate-700 leading-relaxed font-medium">
              {signal.preview}
            </div>
          </div>

          {/* Actions Bar */}
          <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
            <a
              href={signal.gmailUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-blue-600 transition-colors"
            >
              <span>View in Gmail</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>

            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  onAction(signal.id, 'Handled');
                  onClose();
                }}
                className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 shadow-sm transition-all cursor-pointer"
              >
                Mark as Handled
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
