import React, { useState } from 'react';
import { motion } from 'motion/react';
import { Radio, ShieldCheck, Mail, ArrowRight, Sparkles } from 'lucide-react';
import { api } from '../lib/api';

interface AuthScreenProps {
  onLogin: () => void;
}

export const AuthScreen: React.FC<AuthScreenProps> = ({ onLogin }) => {
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleConnect = async () => {
    setIsConnecting(true);
    setError(null);
    try {
      const authUrl = await api.getGoogleAuthUrl();
      window.location.href = authUrl;
    } catch (err: any) {
      console.error('Failed to get Google Auth URL:', err);
      setError(err.message || 'Failed to connect to Google OAuth backend');
      setIsConnecting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6 text-slate-900 font-sans">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-md bg-white border border-slate-200 rounded-3xl p-8 shadow-xl text-center space-y-6"
      >
        {/* App Emblem */}
        <div className="mx-auto w-16 h-16 rounded-2xl bg-blue-600 flex items-center justify-center text-white shadow-md">
          <Radio className="w-8 h-8 animate-pulse" />
        </div>

        {/* Title */}
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-50 border border-blue-100 text-blue-700 text-xs font-bold mb-3 uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5" />
            AI Executive Assistant
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Welcome to Signal
          </h1>
          <p className="text-sm text-slate-600 mt-1.5 leading-relaxed font-medium">
            Turn email overload into clear executive decisions without losing focus.
          </p>
        </div>

        {/* Action Button */}
        <button
          onClick={handleConnect}
          disabled={isConnecting}
          className="w-full py-3.5 px-6 rounded-xl bg-slate-900 hover:bg-slate-800 disabled:opacity-75 text-white font-bold text-sm shadow-md transition-all flex items-center justify-center gap-3 cursor-pointer group"
        >
          {isConnecting ? (
            <div className="flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              <span>Authenticating OAuth...</span>
            </div>
          ) : (
            <>
              <Mail className="w-4 h-4 text-blue-400" />
              <span>Connect Gmail Account</span>
              <ArrowRight className="w-4 h-4 text-slate-400 group-hover:translate-x-1 transition-transform" />
            </>
          )}
        </button>

        {/* Security & Privacy Badges */}
        <div className="pt-2 border-t border-slate-100 space-y-2">
          <div className="flex items-center justify-center gap-2 text-xs font-semibold text-slate-500">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>Read-only metadata analysis</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-normal font-medium">
            Your data is processed strictly in-memory. Zero persistent data retention or third-party sharing.
          </p>
        </div>
      </motion.div>
    </div>
  );
};
