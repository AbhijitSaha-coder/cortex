import React, { useEffect, useState } from 'react';
import {
  Activity,
  Play,
  CheckCircle2,
  TrendingUp,
  Clock,
  Zap,
  DollarSign,
  Layers,
  ShieldAlert,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { EvaluationRun } from '../types';
import { api } from '../api/client';

export const EvaluationsPage: React.FC = () => {
  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [activeRun, setActiveRun] = useState<EvaluationRun | null>(null);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchRuns = async () => {
    try {
      const data = await api.listEvaluationRuns();
      setRuns(data);
      if (data.length > 0 && !activeRun) {
        setActiveRun(data[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, []);

  const handleRunEvaluation = async () => {
    setIsRunning(true);
    try {
      const newRun = await api.runEvaluation(3, 'hybrid');
      setRuns([newRun, ...runs]);
      setActiveRun(newRun);
    } catch (e: any) {
      alert(`Benchmark execution failed: ${e.message || 'Error'}`);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            Evaluation & Observability
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Empirical benchmark measuring Recall@K, Mean Reciprocal Rank (MRR), latency, and groundedness
          </p>
        </div>

        <Button
          variant="primary"
          size="sm"
          icon={<Play className="w-4 h-4" />}
          onClick={handleRunEvaluation}
          isLoading={isRunning}
        >
          Run Benchmark Suite
        </Button>
      </div>

      {/* Metrics Cards */}
      {activeRun ? (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <span className="text-[11px] font-mono text-slate-400 uppercase">Recall @ K (top-3)</span>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-brand-400 font-mono">
                  {(activeRun.recall_at_k * 100).toFixed(1)}%
                </span>
                <span className="text-xs text-slate-500">ground truth match</span>
              </div>
            </Card>

            <Card>
              <span className="text-[11px] font-mono text-slate-400 uppercase">Mean Reciprocal Rank</span>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-emerald-400 font-mono">
                  {activeRun.mrr.toFixed(3)}
                </span>
                <span className="text-xs text-slate-500">MRR score</span>
              </div>
            </Card>

            <Card>
              <span className="text-[11px] font-mono text-slate-400 uppercase">Groundedness Score</span>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-teal-400 font-mono">
                  {(activeRun.groundedness_score * 100).toFixed(0)}%
                </span>
                <span className="text-xs text-slate-500">evidence alignment</span>
              </div>
            </Card>

            <Card>
              <span className="text-[11px] font-mono text-slate-400 uppercase">Avg Response Latency</span>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-100 font-mono">
                  {activeRun.avg_latency_ms.toFixed(1)}ms
                </span>
                <span className="text-xs text-slate-500">end-to-end</span>
              </div>
            </Card>
          </div>

          {/* Detailed per-query results table */}
          <Card className="p-0 overflow-hidden">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <h3 className="text-xs font-semibold uppercase font-mono tracking-wider text-slate-300">
                Benchmark Sample Breakdown ({activeRun.sample_count} Test Queries)
              </h3>
              <span className="text-xs text-slate-500 font-mono">
                Total tokens: {activeRun.total_tokens.toLocaleString()} | Cost: ${activeRun.estimated_cost_usd.toFixed(4)}
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#0b101e] border-b border-slate-800 text-slate-400 font-mono uppercase text-[11px]">
                  <tr>
                    <th className="py-3 px-4">Evaluation Query</th>
                    <th className="py-3 px-4">Recall</th>
                    <th className="py-3 px-4">Reciprocal Rank</th>
                    <th className="py-3 px-4">Latency</th>
                    <th className="py-3 px-4">Groundedness</th>
                    <th className="py-3 px-4">Synthesized Output Snippet</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {activeRun.results?.map((res, i) => (
                    <tr key={i} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3 px-4 font-medium text-slate-200 max-w-xs truncate">
                        {res.query}
                      </td>
                      <td className="py-3 px-4 font-mono text-brand-400">
                        {(res.recall * 100).toFixed(0)}%
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-300">
                        {res.reciprocal_rank.toFixed(2)}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-400">
                        {res.latency_ms}ms
                      </td>
                      <td className="py-3 px-4 font-mono text-emerald-400">
                        {(res.groundedness * 100).toFixed(0)}%
                      </td>
                      <td className="py-3 px-4 text-slate-400 max-w-sm truncate font-mono text-[11px]">
                        {res.generated_answer_snippet}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      ) : (
        <Card className="p-12 text-center space-y-4">
          <Activity className="w-10 h-10 text-brand-400 mx-auto" />
          <h3 className="text-base font-bold text-white">No evaluation runs recorded</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Click "Run Benchmark Suite" above to test your hybrid retrieval, RRF ranking, SSRF protection, and citation groundedness against actual benchmark queries.
          </p>
        </Card>
      )}
    </div>
  );
};

