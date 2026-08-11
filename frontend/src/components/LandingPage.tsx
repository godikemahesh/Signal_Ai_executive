import React, { useState } from 'react';
import { motion } from 'motion/react';
import {
  Radio,
  Sparkles,
  Zap,
  ShieldCheck,
  Brain,
  MessageSquare,
  ArrowRight,
  Flame,
  CheckCircle2,
  Lock,
  Mail,
  Activity,
  ChevronRight,
  Layers,
  BarChart3,
  ExternalLink,
  Clock,
  Briefcase,
  CheckCircle,
  ShieldAlert,
  Bot,
  User,
  Sliders,
  RefreshCw
} from 'lucide-react';
import { cn } from '../lib/utils';

interface LandingPageProps {
  onGetStarted: () => void;
  onSignIn: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onGetStarted, onSignIn }) => {
  const [activeDemoTab, setActiveDemoTab] = useState<'overview' | 'focus' | 'timeline' | 'ai'>('overview');

  const scrollToSection = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.5, ease: 'easeOut' },
    },
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-blue-500/30 overflow-x-hidden">
      {/* Top Sticky Header Navigation */}
      <header className="sticky top-0 z-50 bg-slate-950/80 backdrop-blur-md border-b border-slate-800/80 shadow-lg">
        <div className="max-w-7xl mx-auto px-6 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
            <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
              <Radio className="w-5 h-5 text-white animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xl font-bold tracking-tight text-white">Signal</span>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-blue-950/80 text-blue-400 border border-blue-800/60">
                  AI Executive
                </span>
              </div>
            </div>
          </div>

          <nav className="hidden md:flex items-center gap-8 text-xs font-bold text-slate-300">
            <button onClick={() => scrollToSection('features')} className="hover:text-white transition-colors cursor-pointer">
              Features
            </button>
            <button onClick={() => scrollToSection('demo')} className="hover:text-white transition-colors cursor-pointer">
              Interactive Demo
            </button>
            <button onClick={() => scrollToSection('how-it-works')} className="hover:text-white transition-colors cursor-pointer">
              How It Works
            </button>
            <button onClick={() => scrollToSection('security')} className="hover:text-white transition-colors cursor-pointer">
              Security & Privacy
            </button>
          </nav>

          <div className="flex items-center gap-3">
            <button
              onClick={onSignIn}
              className="px-4 py-2 rounded-xl text-xs font-bold text-slate-300 hover:text-white hover:bg-slate-900 transition-all cursor-pointer"
            >
              Sign In
            </button>
            <button
              onClick={onGetStarted}
              className="px-4 py-2.5 rounded-xl text-xs font-bold text-white bg-blue-600 hover:bg-blue-500 shadow-md shadow-blue-600/30 transition-all flex items-center gap-1.5 cursor-pointer glow-accent"
            >
              <span>Get Started</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-16 pb-20 overflow-hidden bg-slate-950 text-white">
        {/* Background glow effects */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-blue-600/15 blur-[120px] rounded-full pointer-events-none" />
        <div className="absolute top-1/3 right-10 w-[300px] h-[300px] bg-rose-600/10 blur-[100px] rounded-full pointer-events-none" />

        <div className="max-w-6xl mx-auto px-6 relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Left Text Column */}
          <div className="lg:col-span-7 text-left space-y-6">
            <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-[1.1]">
              Turn Email Overload into Clear <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-300 to-blue-500">Executive Action</span>
            </h1>

            <p className="text-base sm:text-lg text-slate-300 max-w-xl leading-relaxed font-normal">
              Signal scans your inbox, extracts critical deadlines, collapses email threads into real-world timelines, and surfaces only what truly needs your decision.
            </p>

            <div className="pt-2 flex flex-col sm:flex-row items-center gap-4">
              <button
                onClick={onGetStarted}
                className="w-full sm:w-auto px-8 py-4 rounded-xl text-sm font-bold text-white bg-blue-600 hover:bg-blue-500 shadow-lg shadow-blue-600/30 transition-all flex items-center justify-center gap-2.5 cursor-pointer glow-accent"
              >
                <Mail className="w-4.5 h-4.5 text-white" />
                <span>Get Started Free</span>
                <ArrowRight className="w-4 h-4" />
              </button>
              <button
                onClick={() => scrollToSection('features')}
                className="w-full sm:w-auto px-6 py-4 rounded-xl text-sm font-bold text-slate-300 bg-slate-900/80 hover:bg-slate-800 hover:text-white border border-slate-800 transition-all flex items-center justify-center gap-2 cursor-pointer backdrop-blur-sm"
              >
                <span>See how it works</span>
                <ChevronRight className="w-4 h-4 text-slate-400" />
              </button>
            </div>

            {/* Quick social proof badges */}
            <div className="pt-4 flex flex-wrap items-center gap-6 text-xs text-slate-400 font-medium">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>100% Read-Only Gmail OAuth</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-blue-400" />
                <span>Zero Storage Retention</span>
              </div>
            </div>
          </div>

          {/* Right Floating Glassmorphic Preview Card */}
          <div className="lg:col-span-5 relative flex justify-center">
            <motion.div
              animate={{ y: [0, -10, 0] }}
              transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut' }}
              className="w-full max-w-md rounded-2xl bg-slate-900/90 border border-slate-700/80 p-5 shadow-2xl backdrop-blur-md relative overflow-hidden group"
            >
              {/* Card top banner glow */}
              <div className="absolute -top-12 -right-12 w-32 h-32 bg-blue-500/20 rounded-full blur-2xl group-hover:bg-blue-500/30 transition-all" />

              {/* Sample SignalCard header */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded-lg bg-blue-950/80 border border-blue-800 text-blue-400">
                    <Briefcase className="w-4 h-4" />
                  </div>
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-tight">
                    Stripe — Backend Engineer
                  </span>
                </div>
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-[11px] font-bold bg-rose-950/80 text-rose-300 border border-rose-800/80">
                  <Flame className="w-3 h-3 text-rose-400" />
                  Do Now
                </span>
              </div>

              <h4 className="text-base font-bold text-white mb-1.5">
                Reply to Stripe recruiter
              </h4>

              <p className="text-xs text-slate-300 leading-relaxed line-clamp-2 mb-3">
                "Hi Mahesh, thanks for your interest! Can you share your availability for next week? We have slots on Tuesday 2 PM..."
              </p>

              <div className="flex items-center gap-1.5 text-xs font-bold text-rose-300 mb-4 bg-rose-950/60 px-2.5 py-1 rounded-lg border border-rose-800/60 w-fit">
                <Clock className="w-3.5 h-3.5 text-rose-400" />
                <span>Fast responder — reply expected today</span>
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-slate-800">
                <span className="text-[11px] text-slate-400 font-medium">Open in Gmail</span>
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-1 rounded-lg text-xs font-medium text-slate-300 bg-slate-800 border border-slate-700">
                    Suggest slots
                  </span>
                  <button
                    onClick={onGetStarted}
                    className="px-3.5 py-1 rounded-lg text-xs font-bold text-white bg-blue-600 hover:bg-blue-500 transition-all shadow-sm cursor-pointer"
                  >
                    Reply now
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Stats & Trust Strip */}
      <section className="py-8 bg-slate-900/90 border-y border-slate-800/80 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between shadow-2xs">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Executive Ratio</p>
              <p className="text-lg font-extrabold text-white mt-0.5">147 <span className="text-xs font-normal text-slate-400">signals →</span> 4 <span className="text-xs font-bold text-blue-400">decisions</span></p>
            </div>
            <div className="p-2 rounded-lg bg-blue-950/80 text-blue-400 border border-blue-800/60">
              <Sparkles className="w-4 h-4" />
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between shadow-2xs">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Priority Triage</p>
              <p className="text-lg font-extrabold text-white mt-0.5">6 <span className="text-xs font-medium text-slate-400">Smart Buckets</span></p>
            </div>
            <div className="p-2 rounded-lg bg-rose-950/80 text-rose-400 border border-rose-800/60">
              <Flame className="w-4 h-4" />
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between shadow-2xs">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Sync Frequency</p>
              <p className="text-lg font-extrabold text-emerald-400 mt-0.5">Real-time <span className="text-xs font-normal text-slate-400">Live Gmail</span></p>
            </div>
            <div className="p-2 rounded-lg bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
              <RefreshCw className="w-4 h-4" />
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between shadow-2xs">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Noise Elimination</p>
              <p className="text-lg font-extrabold text-white mt-0.5">98% <span className="text-xs font-medium text-slate-400">Auto-Filtered</span></p>
            </div>
            <div className="p-2 rounded-lg bg-slate-800 text-slate-300 border border-slate-700">
              <ShieldCheck className="w-4 h-4 text-slate-300" />
            </div>
          </div>
        </div>
      </section>

      {/* Features Showcase Section - 6 Visual Feature Cards */}
      <section id="features" className="py-20 bg-slate-950">
        <div className="max-w-6xl mx-auto px-6 space-y-12">
          <div className="text-center max-w-3xl mx-auto space-y-3">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-400 bg-blue-950/80 px-3 py-1 rounded-full border border-blue-800/60">
              Features Showcase
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
              Built for Absolute Email Control
            </h2>
            <p className="text-base text-slate-400 font-medium">
              Every feature is engineered to eliminate context switching and present clear options.
            </p>
          </div>

          <motion.div
            variants={containerVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-50px' }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          >
            {/* Feature 1: Overview / Live Command Center */}
            <motion.div
              variants={itemVariants}
              className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl hover:border-slate-700 transition-all space-y-4 flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-xl bg-blue-950/80 border border-blue-800 text-blue-400 flex items-center justify-center">
                  <BarChart3 className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-white">
                  Live Command Center
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed font-normal">
                  Instant executive dashboard synthesizing hundreds of signals into key metrics and urgent action cards.
                </p>
              </div>

              {/* Mini Visual Mock */}
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-2 mt-2">
                <div className="flex justify-between items-center text-[11px] text-slate-400 font-bold">
                  <span>Needs Action</span>
                  <span className="text-rose-400 bg-rose-950/80 px-1.5 py-0.5 rounded border border-rose-800">2 New</span>
                </div>
                <div className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-[11px] font-medium text-slate-300 flex justify-between items-center">
                  <span className="truncate">Stripe Recruiter Interview</span>
                  <span className="text-blue-400 font-bold shrink-0">Reply</span>
                </div>
              </div>
            </motion.div>

            {/* Feature 2: Focus / Smart Bucketing */}
            <motion.div
              variants={itemVariants}
              className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl hover:border-slate-700 transition-all space-y-4 flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-xl bg-rose-950/80 border border-rose-800 text-rose-400 flex items-center justify-center">
                  <Flame className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-white">
                  Smart Priority Buckets
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed font-normal">
                  Emails are auto-triaged into human-readable buckets: Do Now, Today, This Week, Waiting, Completed, or Ignored.
                </p>
              </div>

              {/* Mini Visual Mock */}
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-2 mt-2">
                <div className="flex gap-1 overflow-x-auto text-[10px] font-bold">
                  <span className="px-2 py-0.5 bg-rose-950/90 text-rose-300 border border-rose-800 rounded">Do Now</span>
                  <span className="px-2 py-0.5 bg-slate-900 text-slate-400 border border-slate-800 rounded">Today</span>
                  <span className="px-2 py-0.5 bg-slate-900 text-slate-400 border border-slate-800 rounded">Waiting</span>
                </div>
                <div className="p-2 rounded-lg bg-slate-900 border-l-2 border-l-rose-500 border border-slate-800 text-[11px] text-slate-300 font-medium">
                  Google HackerRank Assessment (Due 6 PM)
                </div>
              </div>
            </motion.div>

            {/* Feature 3: Timeline / Life Events */}
            <motion.div
              variants={itemVariants}
              className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl hover:border-slate-700 transition-all space-y-4 flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-xl bg-blue-950/80 border border-blue-800 text-blue-400 flex items-center justify-center">
                  <Activity className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-white">
                  Entity & Order Timelines
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed font-normal">
                  Collapses multi-month email threads into clean sequential lifelines for job applications, Amazon packages, and bills.
                </p>
              </div>

              {/* Mini Visual Mock */}
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5 mt-2 text-[11px]">
                <div className="text-slate-300 font-bold">Google SWE Internship</div>
                <div className="space-y-1 pl-3 border-l-2 border-blue-500 text-slate-400">
                  <div>Aug 3: Application submitted</div>
                  <div className="text-white font-bold">Aug 8: OA link received</div>
                </div>
              </div>
            </motion.div>

            {/* Feature 4: Behavior / Personal Model */}
            <motion.div
              variants={itemVariants}
              className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl hover:border-slate-700 transition-all space-y-4 flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-xl bg-purple-950/80 border border-purple-800 text-purple-400 flex items-center justify-center">
                  <Brain className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-white">
                  Self-Learning Heuristics
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed font-normal">
                  Signal learns your response speeds and habits to automatically adjust priority thresholds over time.
                </p>
              </div>

              {/* Mini Visual Mock */}
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-2 mt-2">
                <div className="flex justify-between items-center text-[10px] font-bold text-slate-400">
                  <span>Learned Rule: Recruiter Mails</span>
                  <span className="text-emerald-400">96% confidence</span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                  <div className="bg-emerald-400 h-1.5 rounded-full w-[96%]" />
                </div>
              </div>
            </motion.div>

            {/* Feature 5: Ask Signal / Natural Language */}
            <motion.div
              variants={itemVariants}
              className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl hover:border-slate-700 transition-all space-y-4 flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-950/80 border border-emerald-800 text-emerald-400 flex items-center justify-center">
                  <MessageSquare className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-white">
                  Natural Language Query
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed font-normal">
                  Ask plain-English questions across all your signals, receipts, and interview schedules.
                </p>
              </div>

              {/* Mini Visual Mock */}
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5 mt-2 text-[11px]">
                <div className="bg-slate-900 p-2 rounded-lg text-slate-300 font-medium border border-slate-800">
                  "Which companies rejected me this month?"
                </div>
                <div className="text-blue-400 font-bold px-1">
                  → 3 rejection signals found & tracked.
                </div>
              </div>
            </motion.div>

            {/* Feature 6: Privacy / Secure */}
            <motion.div
              variants={itemVariants}
              className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl hover:border-slate-700 transition-all space-y-4 flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 text-slate-200 flex items-center justify-center">
                  <Lock className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-white">
                  Read-Only Privacy Shield
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed font-normal">
                  Strict OAuth read-only permissions. Zero permanent retention of email body contents.
                </p>
              </div>

              {/* Mini Visual Mock */}
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between text-[11px] text-slate-300 mt-2">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span className="font-bold">OAuth 2.0 Protected</span>
                </div>
                <span className="text-slate-500 font-mono text-[10px]">Read-only</span>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="py-20 bg-slate-900/80 border-t border-slate-800">
        <div className="max-w-5xl mx-auto px-6 space-y-12">
          <div className="text-center max-w-2xl mx-auto space-y-2">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-400 bg-blue-950/80 px-2.5 py-1 rounded-md border border-blue-800/60">
              Simple Workflow
            </span>
            <h2 className="text-3xl font-bold text-white tracking-tight">
              Get Started in 30 Seconds
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative">
            {/* Connecting line for desktop */}
            <div className="hidden md:block absolute top-1/2 left-1/6 right-1/6 h-0.5 bg-gradient-to-r from-blue-600 via-indigo-500 to-emerald-500 -translate-y-6 pointer-events-none z-0" />

            {/* Step 1 */}
            <div className="bg-slate-950 p-6 rounded-2xl border border-slate-800 shadow-xl text-center space-y-3 relative z-10">
              <div className="w-12 h-12 rounded-2xl bg-blue-600 text-white font-bold text-lg flex items-center justify-center mx-auto shadow-md shadow-blue-600/30">
                1
              </div>
              <h3 className="text-base font-bold text-white">Connect Gmail</h3>
              <p className="text-xs text-slate-400 leading-relaxed font-normal">
                Grant secure read-only permission using official Google OAuth 2.0.
              </p>
            </div>

            {/* Step 2 */}
            <div className="bg-slate-950 p-6 rounded-2xl border border-slate-800 shadow-xl text-center space-y-3 relative z-10">
              <div className="w-12 h-12 rounded-2xl bg-indigo-600 text-white font-bold text-lg flex items-center justify-center mx-auto shadow-md shadow-indigo-600/30">
                2
              </div>
              <h3 className="text-base font-bold text-white">Signal Reads & Categorizes</h3>
              <p className="text-xs text-slate-400 leading-relaxed font-normal">
                AI triages incoming items into Do Now, Today, and Timeline views in real-time.
              </p>
            </div>

            {/* Step 3 */}
            <div className="bg-slate-950 p-6 rounded-2xl border border-slate-800 shadow-xl text-center space-y-3 relative z-10">
              <div className="w-12 h-12 rounded-2xl bg-emerald-600 text-white font-bold text-lg flex items-center justify-center mx-auto shadow-md shadow-emerald-600/30">
                3
              </div>
              <h3 className="text-base font-bold text-white">You See Only What Matters</h3>
              <p className="text-xs text-slate-400 leading-relaxed font-normal">
                Execute decisions in seconds without wading through promotional noise.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Security & Privacy Callout */}
      <section id="security" className="py-16 bg-slate-950 border-t border-slate-800">
        <div className="max-w-4xl mx-auto px-6 text-center space-y-6">
          <div className="w-12 h-12 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center text-emerald-400 mx-auto shadow-md">
            <Lock className="w-6 h-6" />
          </div>

          <h2 className="text-3xl font-extrabold text-white tracking-tight">
            Security & Privacy First
          </h2>

          <p className="text-sm text-slate-300 leading-relaxed max-w-2xl mx-auto font-normal">
            Signal is built on read-only API access. We parse metadata and text signals strictly in-memory to synthesize actionable intelligence.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 text-left">
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
              <h4 className="text-xs font-bold text-white uppercase">Read-Only Scopes</h4>
              <p className="text-[11px] text-slate-400">Strictly limited to reading incoming messages.</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
              <h4 className="text-xs font-bold text-white uppercase">In-Memory Parsing</h4>
              <p className="text-[11px] text-slate-400">No persistent storage of email bodies on servers.</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
              <h4 className="text-xs font-bold text-white uppercase">OAuth 2.0 Auth</h4>
              <p className="text-[11px] text-slate-400">Directly authenticated via official Google consent.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA Section */}
      <section className="py-20 bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-white relative overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[250px] bg-blue-600/20 blur-[100px] rounded-full pointer-events-none" />

        <div className="max-w-4xl mx-auto px-6 text-center relative z-10 space-y-6">
          <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white">
            Ready to Experience Email Clarity?
          </h2>

          <p className="text-base text-slate-300 max-w-xl mx-auto font-normal">
            Connect your Gmail account in 30 seconds and reclaim hours of lost focus every week.
          </p>

          <div className="pt-2">
            <button
              onClick={onGetStarted}
              className="px-9 py-4 rounded-xl text-sm font-bold text-white bg-blue-600 hover:bg-blue-500 shadow-xl shadow-blue-600/40 transition-all inline-flex items-center gap-2.5 cursor-pointer glow-accent"
            >
              <Mail className="w-4.5 h-4.5 text-white" />
              <span>Connect Gmail & Launch Workspace</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          <p className="text-xs text-slate-400 font-medium pt-2">
            100% read-only OAuth permission • No emails stored permanently • Cancel anytime
          </p>
        </div>
      </section>

      {/* Minimal Footer */}
      <footer className="bg-slate-950 text-slate-400 py-10 border-t border-slate-900 text-xs">
        <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold">
              <Radio className="w-4 h-4" />
            </div>
            <span className="text-sm font-bold text-white tracking-tight">Signal AI</span>
            <span className="text-slate-500 font-medium">| Executive Assistant Workspace</span>
          </div>

          <p className="text-slate-500 font-medium text-center sm:text-right">
            © 2026 Signal AI. Built with Google AI Studio. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
};
