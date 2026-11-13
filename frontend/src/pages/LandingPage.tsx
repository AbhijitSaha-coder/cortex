import React from 'react';
import { Link } from 'react-router-dom';
import {
  Sparkles,
  Search,
  Bot,
  FileCheck,
  ShieldCheck,
  Zap,
  ArrowRight,
  Database,
  BarChart3,
  Bookmark,
} from 'lucide-react';
import { Button } from '../components/common/Button';

export const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col justify-between selection:bg-brand-500 selection:text-white">
      {/* Top Navbar */}
      <header className="border-b border-slate-800/80 sticky top-0 z-40 bg-[#090d16]/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-brand-600 to-emerald-400 flex items-center justify-center shadow-lg shadow-brand-500/20 text-white font-bold">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-lg tracking-tight text-white">Cortex</span>
          </div>

          <div className="flex items-center gap-4">
            <Link to="/login">
              <Button variant="ghost" size="sm">
                Sign In
              </Button>
            </Link>
            <Link to="/register">
              <Button variant="primary" size="sm">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-20 pb-16 px-6 max-w-5xl mx-auto text-center space-y-8">
        <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full text-xs font-semibold bg-brand-500/10 text-brand-400 border border-brand-500/20 shadow-sm animate-pulse">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Next-Generation AI Knowledge & Research Engine</span>
        </div>

        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-white leading-tight">
          Supercharge your research with an{' '}
          <span className="bg-gradient-to-r from-brand-400 via-emerald-300 to-teal-400 bg-clip-text text-transparent">
            Agentic Knowledge Platform
          </span>
        </h1>

        <p className="text-base md:text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
          Ingest PDFs, TXT, Markdown, and web pages into a high-dimensional vector space.
          Execute hybrid RRF retrieval, perform bounded multi-tool agentic workflows, and generate citation-grounded research reports.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          <Link to="/register">
            <Button size="lg" variant="primary" icon={<ArrowRight className="w-4 h-4" />}>
              Launch Research Workspace
            </Button>
          </Link>
          <Link to="/login">
            <Button size="lg" variant="secondary">
              Sign In to Existing Vault
            </Button>
          </Link>
        </div>

        {/* Product Preview Card */}
        <div className="mt-12 p-1.5 rounded-2xl bg-gradient-to-b from-slate-700/60 to-slate-900 border border-slate-800 shadow-2xl">
          <div className="rounded-xl bg-[#0b101d] p-6 text-left space-y-4 border border-slate-800/80">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500/70" />
                <div className="w-3 h-3 rounded-full bg-amber-500/70" />
                <div className="w-3 h-3 rounded-full bg-emerald-500/70" />
                <span className="text-xs text-slate-500 font-mono ml-2">cortex-research-session.rag</span>
              </div>
              <span className="text-xs font-mono text-brand-400 bg-brand-500/10 px-2 py-0.5 rounded border border-brand-500/20">
                Hybrid RRF + Agent Loop Active
              </span>
            </div>

            <div className="space-y-3 font-sans text-xs">
              <div className="p-3 rounded-lg bg-slate-900/90 text-slate-300 border border-slate-800">
                <span className="text-brand-400 font-semibold block mb-1">User Research Task:</span>
                "Analyze the scalability limits of transformer attention mechanisms and compare empirical mitigation techniques."
              </div>
              <div className="p-3.5 rounded-lg bg-[#070b14] text-slate-200 border border-brand-500/30 space-y-2">
                <div className="flex items-center gap-2 text-brand-400 font-semibold">
                  <Bot className="w-4 h-4" />
                  <span>Cortex Research Agent:</span>
                </div>
                <p className="leading-relaxed">
                  According to recent benchmarks, standard self-attention complexity scales quadratically with sequence length{' '}
                  <span className="px-1.5 py-0.5 rounded text-[10px] bg-brand-500/20 text-brand-300 font-mono border border-brand-500/30">
                    [Citation 1: AttentionIsAllYouNeed.pdf, p.4]
                  </span>
                  . FlashAttention mitigated memory bottlenecks by fusing GPU kernel operations{' '}
                  <span className="px-1.5 py-0.5 rounded text-[10px] bg-brand-500/20 text-brand-300 font-mono border border-brand-500/30">
                    [Citation 2: FlashAttention_Paper.pdf, p.2]
                  </span>
                  .
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Grid */}
      <section className="py-16 px-6 max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="w-10 h-10 rounded-xl bg-brand-500/10 text-brand-400 flex items-center justify-center border border-brand-500/20">
            <Database className="w-5 h-5" />
          </div>
          <h3 className="font-semibold text-slate-100 text-base">Hybrid Search with RRF</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Combines dense pgvector cosine embeddings with sparse PostgreSQL full-text retrieval, fused via Reciprocal Rank Fusion and refined with cross-encoder reranking.
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center border border-emerald-500/20">
            <Bot className="w-5 h-5" />
          </div>
          <h3 className="font-semibold text-slate-100 text-base">Controlled Agent Loops</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Autonomous multi-tool agent capable of searching knowledge bases, comparing documents, uncovering contradictions, and identifying unanswered questions with strict execution timeouts.
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="w-10 h-10 rounded-xl bg-teal-500/10 text-teal-400 flex items-center justify-center border border-teal-500/20">
            <BarChart3 className="w-5 h-5" />
          </div>
          <h3 className="font-semibold text-slate-100 text-base">Empirical RAG Benchmark</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Built-in automated evaluation suite calculating actual Recall@K, Mean Reciprocal Rank (MRR), citation precision, response latencies, and token cost economics.
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-8 px-6 text-center text-xs text-slate-500">
        <p>© 2026 Cortex — AI Research & Knowledge Agent. Production-grade software architecture.</p>
      </footer>
    </div>
  );
};
