import React, { useState } from 'react';
import { motion } from 'motion/react';
import { Entity } from '../lib/data';
import {
  Building2,
  Briefcase,
  Package,
  FileText,
  Search,
  ChevronRight,
  Clock,
  Layers,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { cn } from '../lib/utils';

interface TimelineScreenProps {
  entities: Entity[];
}

export const TimelineScreen: React.FC<TimelineScreenProps> = ({ entities }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'interview' | 'order' | 'general'>('all');
  const [expandedEntityId, setExpandedEntityId] = useState<string | null>(null);

  const filteredEntities = entities.filter((e) => {
    const matchesSearch = e.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      e.type.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || e.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const getEntityIcon = (type: Entity['type']) => {
    switch (type) {
      case 'interview':
        return <Briefcase className="w-4 h-4 text-blue-600" />;
      case 'order':
        return <Package className="w-4 h-4 text-emerald-600" />;
      case 'bill':
        return <FileText className="w-4 h-4 text-rose-600" />;
      default:
        return <Building2 className="w-4 h-4 text-slate-600" />;
    }
  };

  const getBadgeColor = (type: Entity['type']) => {
    switch (type) {
      case 'interview':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'order':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'bill':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Entity Timelines
          </h1>
          <p className="text-xs text-slate-600 mt-0.5 font-medium">
            Collapses multi-month email threads into clean, compact entity cards.
          </p>
        </div>
        <div className="text-xs text-slate-500 font-bold bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200 w-fit">
          {filteredEntities.length} active timelines
        </div>
      </div>

      {/* Search and Category Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search entities (e.g., Stripe, Amazon)..."
            className="w-full pl-10 pr-4 py-2 bg-white border border-slate-200/90 rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all shadow-2xs font-medium"
          />
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar">
          {(['all', 'interview', 'order', 'general'] as const).map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={cn(
                "px-3 py-1.5 rounded-lg text-xs font-bold capitalize transition-all cursor-pointer whitespace-nowrap border",
                selectedCategory === cat
                  ? "bg-slate-900 text-white border-slate-900 shadow-sm"
                  : "bg-white border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-50 shadow-2xs"
              )}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Entity Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredEntities.map((entity) => {
          const isExpanded = expandedEntityId === entity.id;
          const eventsToShow = isExpanded ? entity.events : entity.events.slice(-2); // show latest events by default

          return (
            <motion.div
              key={entity.id}
              layout
              className="bg-white border border-slate-200/90 hover:border-slate-300 rounded-2xl p-4 shadow-2xs hover:shadow-md transition-all flex flex-col justify-between space-y-3"
            >
              {/* Card Header */}
              <div className="space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-xl bg-slate-50 border border-slate-200/80 shrink-0">
                      {getEntityIcon(entity.type)}
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-slate-900 tracking-tight line-clamp-1">
                        {entity.name}
                      </h3>
                      <div className="flex items-center gap-1.5 mt-0.5">
                        <span className={cn("text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border", getBadgeColor(entity.type))}>
                          {entity.type}
                        </span>
                        <span className="text-[10px] text-slate-400 font-medium flex items-center gap-1">
                          <Clock className="w-3 h-3 text-slate-400" />
                          {entity.lastUpdated}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Event Stepper / Timeline inside Card */}
                <div className="pt-2">
                  <div className="relative pl-4 space-y-2.5 before:absolute before:left-1.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
                    {eventsToShow.map((evt, idx) => {
                      const isLatest = idx === eventsToShow.length - 1;

                      return (
                        <div key={evt.id} className="relative group">
                          {/* Indicator Node */}
                          <span
                            className={cn(
                              "absolute -left-4 top-1.5 w-2 h-2 rounded-full border border-white ring-2 shrink-0 transition-all",
                              isLatest
                                ? "bg-blue-600 ring-blue-100"
                                : "bg-slate-400 ring-slate-100"
                            )}
                          />

                          <div className={cn(
                            "p-2.5 rounded-xl border text-xs transition-all",
                            isLatest
                              ? "bg-blue-50/60 border-blue-200/80"
                              : "bg-slate-50/80 border-slate-200/70"
                          )}>
                            <div className="flex items-center justify-between text-[11px] mb-0.5">
                              <span className={cn("font-bold truncate max-w-[170px]", isLatest ? "text-blue-900" : "text-slate-700")}>
                                {evt.subject}
                              </span>
                              <span className="font-mono text-[10px] text-slate-400 shrink-0">{evt.timestamp}</span>
                            </div>
                            <p className="text-[11px] text-slate-600 line-clamp-2 leading-relaxed font-medium">
                              {evt.summary}
                            </p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Card Footer Actions */}
              <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
                <span className="text-[11px] text-slate-500 font-medium flex items-center gap-1">
                  <Layers className="w-3.5 h-3.5 text-slate-400" />
                  {entity.events.length} Mails
                </span>

                {entity.events.length > 2 && (
                  <button
                    onClick={() => setExpandedEntityId(isExpanded ? null : entity.id)}
                    className="text-[11px] font-bold text-blue-600 hover:text-blue-700 hover:bg-blue-50 px-2.5 py-1 rounded-lg transition-colors flex items-center gap-1 cursor-pointer"
                  >
                    <span>{isExpanded ? 'Collapse' : `+${entity.events.length - 2} earlier`}</span>
                    {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                  </button>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
};

