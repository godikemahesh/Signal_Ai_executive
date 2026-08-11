import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'motion/react';
import { ChatMessage, suggestedPrompts } from '../lib/data';
import { Send, Bot, User, Sparkles, Loader2, ArrowUpRight } from 'lucide-react';
import { cn } from '../lib/utils';

interface AskSignalScreenProps {
  chatHistory: ChatMessage[];
  onSendMessage: (text: string) => void;
  isThinking?: boolean;
}

export const AskSignalScreen: React.FC<AskSignalScreenProps> = ({
  chatHistory,
  onSendMessage,
  isThinking = false
}) => {
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, isThinking]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;
    onSendMessage(inputText.trim());
    setInputText('');
  };

  const handlePromptClick = (promptText: string) => {
    onSendMessage(promptText);
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
          Ask Signal Anything
        </h1>
        <p className="text-sm text-slate-600 mt-0.5 font-medium">
          Query across all your 147 signals, emails, receipts, and interview schedules in natural language.
        </p>
      </div>

      {/* Suggested Prompt Chips */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 no-scrollbar">
        {suggestedPrompts.map((p) => (
          <button
            key={p.id}
            onClick={() => handlePromptClick(p.text)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-white border border-slate-200 text-slate-700 hover:text-slate-900 hover:bg-slate-50 hover:border-slate-300 transition-all cursor-pointer shrink-0 shadow-2xs group"
          >
            <Sparkles className="w-3.5 h-3.5 text-blue-600 shrink-0" />
            <span>{p.text}</span>
            <ArrowUpRight className="w-3 h-3 text-slate-400 group-hover:text-slate-700 transition-colors" />
          </button>
        ))}
      </div>

      {/* Chat Messages Box */}
      <div className="rounded-2xl bg-white border border-slate-200/90 p-5 shadow-sm min-h-[380px] max-h-[500px] overflow-y-auto space-y-4 flex flex-col">
        {chatHistory.length === 0 ? (
          <div className="m-auto text-center py-12 text-slate-400">
            <Bot className="w-10 h-10 mx-auto mb-2 text-slate-300" />
            <p className="text-sm font-semibold text-slate-600">Start a conversation with Signal</p>
            <p className="text-xs text-slate-400 font-medium mt-1">Try one of the suggested prompts above.</p>
          </div>
        ) : (
          chatHistory.map((msg) => (
            <div
              key={msg.id}
              className={cn(
                "flex items-start gap-3 max-w-[85%]",
                msg.role === 'user' ? "ml-auto flex-row-reverse" : "mr-auto"
              )}
            >
              <div
                className={cn(
                  "w-7 h-7 rounded-lg flex items-center justify-center shrink-0 text-xs font-bold shadow-2xs",
                  msg.role === 'user'
                    ? "bg-slate-900 text-white"
                    : "bg-blue-600 text-white"
                )}
              >
                {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div
                className={cn(
                  "p-3.5 rounded-2xl text-sm leading-relaxed",
                  msg.role === 'user'
                    ? "bg-slate-900 text-white font-medium"
                    : "bg-slate-100 text-slate-800 border border-slate-200/80 font-medium whitespace-pre-wrap shadow-2xs"
                )}
              >
                {msg.content}
              </div>
            </div>
          ))
        )}

        {isThinking && (
          <div className="flex items-center gap-3 mr-auto max-w-[80%]">
            <div className="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center shrink-0">
              <Bot className="w-4 h-4" />
            </div>
            <div className="p-3.5 rounded-2xl bg-slate-100 border border-slate-200/80 text-slate-600 text-xs font-medium flex items-center gap-2">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-600" />
              <span>Analyzing signals & draft history...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Box */}
      <form onSubmit={handleSubmit} className="flex items-center gap-2">
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Ask anything about your emails, updates, due dates..."
          className="flex-1 px-4 py-3 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all shadow-2xs font-medium"
        />
        <button
          type="submit"
          disabled={!inputText.trim() || isThinking}
          className="px-5 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold text-sm shadow-sm transition-all flex items-center gap-2 cursor-pointer"
        >
          <span>Send</span>
          <Send className="w-4 h-4" />
        </button>
      </form>
    </motion.div>
  );
};
