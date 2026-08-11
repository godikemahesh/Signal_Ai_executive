import React from 'react';
import { motion } from 'motion/react';
import { BehaviorInsight } from '../lib/data';
import { Brain, CheckCircle2, Sliders, ShieldCheck, Zap } from 'lucide-react';

interface BehaviorScreenProps {
  insights: BehaviorInsight[];
  behaviorData?: any;
}

export const BehaviorScreen: React.FC<BehaviorScreenProps> = ({ insights, behaviorData }) => {
  const displayInsights = behaviorData?.insights?.length ? behaviorData.insights : insights;
  const autoFiltered = behaviorData?.auto_filtered_pct !== undefined ? behaviorData.auto_filtered_pct : 84.2;
  const rulesCount = behaviorData?.learned_rules_count !== undefined ? behaviorData.learned_rules_count : 12;
  const timeSaved = behaviorData?.time_saved_hours !== undefined ? behaviorData.time_saved_hours : 4.5;

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
          Behavioral Learning Engine
        </h1>
        <p className="text-sm text-slate-600 mt-0.5 font-medium">
          Signal adapts to how you handle emails over time. Here is what it learned from your history.
        </p>
      </div>

      {/* Hero Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="p-4 rounded-xl bg-white border border-slate-200/90 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Auto-Filtered</p>
          <p className="text-2xl font-bold text-blue-600 mt-1">{autoFiltered}%</p>
          <p className="text-xs text-slate-500 mt-0.5">Emails handled without nagging</p>
        </div>

        <div className="p-4 rounded-xl bg-white border border-slate-200/90 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Learned Patterns</p>
          <p className="text-2xl font-bold text-emerald-600 mt-1">{rulesCount} Rules</p>
          <p className="text-xs text-slate-500 mt-0.5">Active behavioral heuristics</p>
        </div>

        <div className="p-4 rounded-xl bg-white border border-slate-200/90 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Time Saved</p>
          <p className="text-2xl font-bold text-amber-600 mt-1">~{timeSaved} hrs</p>
          <p className="text-xs text-slate-500 mt-0.5">Saved this week</p>
        </div>
      </div>

      {/* Learned Heuristics List */}
      <div className="space-y-4">
        {displayInsights.map((insight: any) => (
          <div
            key={insight.id}
            className="rounded-2xl bg-white border border-slate-200/90 p-5 shadow-sm space-y-3"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-xl bg-blue-50 border border-blue-100 text-blue-600 shrink-0 mt-0.5">
                  <Brain className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">
                    {insight.pattern}
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5 font-medium">
                    Observed over {insight.confidence}% of similar interactions
                  </p>
                </div>
              </div>

              <span className="shrink-0 px-2.5 py-1 rounded-lg text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                {insight.impact}
              </span>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed font-medium bg-slate-50/80 p-3 rounded-xl border border-slate-200/80">
              <strong className="text-slate-800">Automated Action:</strong> {insight.actionTaken}
            </p>

            <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono font-medium pt-1">
              <span>Rule ID: {insight.id}</span>
              <span>Confidence score: {(insight.confidence / 100).toFixed(2)}</span>
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
};
