import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FileText,
  Layers,
  Bot,
  FileCheck,
  HardDrive,
  UploadCloud,
  Globe,
  Sparkles,
  ArrowRight,
  Clock,
  CheckCircle2,
  AlertCircle,
  Database,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { DashboardStats } from '../types';
import { api } from '../api/client';
import { UploadModal } from '../components/documents/UploadModal';
import { URLImportModal } from '../components/documents/URLImportModal';

export const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isUploadOpen, setIsUploadOpen] = useState<boolean>(false);
  const [isUrlOpen, setIsUrlOpen] = useState<boolean>(false);

  const fetchStats = async () => {
    try {
      const data = await api.getDashboardStats();
      setStats(data);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const statCards = [
    {
      label: 'Indexed Documents',
      value: stats?.total_documents ?? 0,
      sub: `${stats?.processed_documents ?? 0} vectorized`,
      icon: FileText,
      color: 'text-brand-400 bg-brand-500/10 border-brand-500/20',
    },
    {
      label: 'Vector Chunks',
      value: stats?.total_chunks ?? 0,
      sub: 'Embeddings indexed',
      icon: Layers,
      color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    },
    {
      label: 'Research Sessions',
      value: stats?.total_conversations ?? 0,
      sub: 'Active conversations',
      icon: Bot,
      color: 'text-teal-400 bg-teal-500/10 border-teal-500/20',
    },
    {
      label: 'Research Reports',
      value: stats?.total_reports ?? 0,
      sub: 'Grounded syntheses',
      icon: FileCheck,
      color: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
    },
  ];

  return (
    <div className="space-y-8">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            Knowledge Dashboard
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time status of your high-dimensional RAG memory and autonomous research agents
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="secondary"
            size="sm"
            icon={<Globe className="w-4 h-4 text-slate-300" />}
            onClick={() => setIsUrlOpen(true)}
          >
            Import URL
          </Button>
          <Button
            variant="primary"
            size="sm"
            icon={<UploadCloud className="w-4 h-4" />}
            onClick={() => setIsUploadOpen(true)}
          >
            Upload File
          </Button>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <Card key={idx} className="relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">{card.label}</span>
                <div className={`p-2 rounded-xl border ${card.color}`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-4">
                <span className="text-2xl font-bold text-white tracking-tight">
                  {isLoading ? '...' : card.value}
                </span>
                <span className="block text-[11px] text-slate-500 mt-0.5">{card.sub}</span>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Quick Launch & Architecture Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Workspace Quick Launch */}
        <div className="lg:col-span-2 space-y-6">
          <div className="p-6 rounded-2xl bg-gradient-to-r from-brand-950/40 via-slate-900 to-slate-900 border border-brand-500/20 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div className="space-y-2 max-w-lg">
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-brand-500/15 text-brand-300 border border-brand-500/30">
                <Sparkles className="w-3 h-3 text-brand-400" />
                <span>Autonomous Agent Ready</span>
              </div>
              <h3 className="text-lg font-bold text-white">Ask Cortex anything across your library</h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Execute hybrid RRF retrieval, run tool loops to cross-reference multiple papers, and generate structured evidence citations.
              </p>
            </div>
            <Link to="/workspace">
              <Button variant="primary" icon={<ArrowRight className="w-4 h-4" />}>
                Launch Workspace
              </Button>
            </Link>
          </div>

          {/* Recent Ingestion Activity */}
          <Card>
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
              <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                <Clock className="w-4 h-4 text-slate-400" />
                <span>Recent Knowledge Additions</span>
              </h3>
              <Link to="/library" className="text-xs text-brand-400 hover:text-brand-300 font-medium">
                View all library
              </Link>
            </div>

            {isLoading ? (
              <div className="space-y-3 animate-pulse">
                <div className="h-10 bg-slate-800/40 rounded-xl" />
                <div className="h-10 bg-slate-800/40 rounded-xl" />
              </div>
            ) : stats?.recent_activity.length ? (
              <div className="divide-y divide-slate-800/60">
                {stats.recent_activity.map((act) => (
                  <div key={act.id} className="py-3 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-3 overflow-hidden">
                      <FileText className="w-4 h-4 text-brand-400 flex-shrink-0" />
                      <div className="truncate">
                        <span className="font-medium text-slate-200 block truncate">{act.title}</span>
                        <span className="text-[11px] text-slate-500">{act.extra}</span>
                      </div>
                    </div>
                    <Badge variant={act.status === 'completed' ? 'success' : 'warning'}>
                      {act.status}
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 text-center py-6">
                No documents added yet. Click "Upload File" above to get started.
              </p>
            )}
          </Card>
        </div>

        {/* Engine Pipeline Status */}
        <div className="space-y-6">
          <Card className="space-y-4">
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <Database className="w-4 h-4 text-brand-400" />
              <span>Pipeline Architecture</span>
            </h3>

            <div className="space-y-3 text-xs">
              <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="font-medium text-slate-200 block">Hybrid Search (RRF)</span>
                  <span className="text-[11px] text-slate-500">Vector + Full-Text Rank Fusion</span>
                </div>
                <Badge variant="success">Active</Badge>
              </div>

              <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="font-medium text-slate-200 block">Cross-Encoder Reranker</span>
                  <span className="text-[11px] text-slate-500">Candidate relevance optimization</span>
                </div>
                <Badge variant="success">Active</Badge>
              </div>

              <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="font-medium text-slate-200 block">SSRF Security Guard</span>
                  <span className="text-[11px] text-slate-500">Private CIDR blocking</span>
                </div>
                <Badge variant="success">Secured</Badge>
              </div>

              <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="font-medium text-slate-200 block">Prompt Injection Filter</span>
                  <span className="text-[11px] text-slate-500">Strict XML delimiter boundaries</span>
                </div>
                <Badge variant="success">Secured</Badge>
              </div>
            </div>
          </Card>
        </div>
      </div>

      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploaded={fetchStats}
      />
      <URLImportModal
        isOpen={isUrlOpen}
        onClose={() => setIsUrlOpen(false)}
        onImported={fetchStats}
      />
    </div>
  );
};
