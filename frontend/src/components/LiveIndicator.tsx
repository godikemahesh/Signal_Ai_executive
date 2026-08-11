import React, { useState, useEffect } from 'react';
import { RefreshCw } from 'lucide-react';
import { cn } from '../lib/utils';

interface LiveIndicatorProps {
  onSync?: () => void;
  isSyncing?: boolean;
}

export const LiveIndicator: React.FC<LiveIndicatorProps> = ({ onSync, isSyncing = false }) => {
  const [secondsAgo, setSecondsAgo] = useState(2);

  useEffect(() => {
    const interval = setInterval(() => {
      setSecondsAgo((prev) => (prev > 30 ? 2 : prev + 1));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleManualSync = () => {
    setSecondsAgo(0);
    if (onSync) onSync();
  };

  return (
    <button
      onClick={handleManualSync}
      title="Click to trigger immediate Gmail sync"
      className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 text-xs text-slate-300 hover:text-white hover:border-slate-600 transition-all cursor-pointer group shadow-2xs"
    >
      <span className="relative flex h-2 w-2">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
        <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
      </span>
      <span className="font-medium">
        {isSyncing ? 'Syncing Gmail...' : `Live · updated ${secondsAgo}s ago`}
      </span>
      <RefreshCw className={cn("w-3 h-3 text-slate-400 group-hover:text-blue-400 transition-transform", isSyncing && "animate-spin text-blue-400")} />
    </button>
  );
};
