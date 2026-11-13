import React, { useEffect, useState } from 'react';
import {
  FileText,
  Plus,
  Download,
  Trash2,
  BookOpen,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Bookmark,
  Calendar,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { Input } from '../components/common/Input';
import { ResearchReport } from '../types';
import { api } from '../api/client';

export const ReportsPage: React.FC = () => {
  const [reports, setReports] = useState<ResearchReport[]>([]);
  const [selectedReport, setSelectedReport] = useState<ResearchReport | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);

  // Form fields
  const [question, setQuestion] = useState<string>('');
  const [title, setTitle] = useState<string>('');
  const [focusAreas, setFocusAreas] = useState<string>('');

  const fetchReports = async () => {
    try {
      const data = await api.listReports();
      setReports(data);
      if (data.length > 0 && !selectedReport) {
        setSelectedReport(data[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;
    setIsGenerating(true);
    try {
      const areas = focusAreas
        ? focusAreas.split(',').map((s) => s.trim()).filter(Boolean)
        : undefined;
      const report = await api.generateReport({
        research_question: question,
        title: title || undefined,
        focus_areas: areas,
      });
      setReports([report, ...reports]);
      setSelectedReport(report);
      setIsModalOpen(false);
      setQuestion('');
      setTitle('');
      setFocusAreas('');
    } catch (e: any) {
      alert(`Report generation failed: ${e.message || 'Unknown error'}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleExportMarkdown = async (report: ResearchReport) => {
    try {
      const md = await api.exportReportMarkdown(report.id);
      const blob = new Blob([md], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${report.title.replace(/[^a-zA-Z0-9_-]/g, '_')}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      alert('Failed to download report');
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('Delete this research report?')) return;
    try {
      await api.deleteReport(id);
      setReports(reports.filter((r) => r.id !== id));
      if (selectedReport?.id === id) {
        setSelectedReport(reports[1] || null);
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Research Reports</h1>
          <p className="text-xs text-slate-400 mt-1">
            Deep-dive multi-source structured reports with verifiable citations and Markdown exports
          </p>
        </div>

        <Button
          variant="primary"
          size="sm"
          icon={<Plus className="w-4 h-4" />}
          onClick={() => setIsModalOpen(true)}
        >
          Generate New Report
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Reports Index */}
        <Card className="p-4 space-y-3 lg:col-span-1 h-[calc(100vh-14rem)] flex flex-col justify-between">
          <h3 className="text-xs font-semibold uppercase font-mono tracking-wider text-slate-400 pb-2 border-b border-slate-800">
            Saved Reports ({reports.length})
          </h3>

          <div className="flex-1 overflow-y-auto space-y-2 pr-1">
            {isLoading ? (
              <p className="text-xs text-slate-500 py-6 text-center">Loading reports...</p>
            ) : reports.length === 0 ? (
              <p className="text-xs text-slate-500 py-6 text-center">
                No reports generated yet. Click "Generate New Report" to start.
              </p>
            ) : (
              reports.map((report) => {
                const isSelected = selectedReport?.id === report.id;
                return (
                  <div
                    key={report.id}
                    onClick={() => setSelectedReport(report)}
                    className={`p-3 rounded-xl border text-xs cursor-pointer transition-all space-y-1.5 ${
                      isSelected
                        ? 'bg-slate-800 border-brand-500/50 shadow-sm'
                        : 'bg-slate-900/70 border-slate-800/80 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="font-semibold text-slate-100 line-clamp-2">
                        {report.title}
                      </span>
                      <button
                        onClick={(e) => handleDelete(report.id, e)}
                        className="text-slate-500 hover:text-red-400 transition-colors p-0.5"
                        title="Delete"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-slate-500 font-mono">
                      <span>{new Date(report.created_at).toLocaleDateString()}</span>
                      <Badge variant="success">completed</Badge>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </Card>

        {/* Report Content Viewer */}
        <Card className="lg:col-span-2 h-[calc(100vh-14rem)] flex flex-col justify-between overflow-hidden">
          {selectedReport ? (
            <>
              {/* Report Header Bar */}
              <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                <div className="overflow-hidden">
                  <h2 className="text-lg font-bold text-white truncate">{selectedReport.title}</h2>
                  <span className="text-[11px] text-slate-400 font-mono">
                    Created on {new Date(selectedReport.created_at).toLocaleDateString()}
                  </span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  icon={<Download className="w-3.5 h-3.5" />}
                  onClick={() => handleExportMarkdown(selectedReport)}
                >
                  Export Markdown
                </Button>
              </div>

              {/* Structured Sections Reader */}
              <div className="flex-1 overflow-y-auto py-6 space-y-6 text-xs text-slate-300 leading-relaxed pr-2 font-sans">
                {/* 1. Research Question */}
                <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800">
                  <h4 className="font-bold text-brand-400 uppercase tracking-wider text-[11px] mb-1 font-mono">
                    1. Primary Research Question
                  </h4>
                  <p className="text-sm text-slate-100 font-medium">{selectedReport.research_question}</p>
                </div>

                {/* 2. Executive Summary */}
                {selectedReport.executive_summary && (
                  <div className="space-y-2">
                    <h4 className="font-bold text-white text-sm">2. Executive Summary</h4>
                    <p className="p-4 rounded-xl bg-[#080c18] border border-slate-800/80">
                      {selectedReport.executive_summary}
                    </p>
                  </div>
                )}

                {/* 3. Main Findings */}
                {selectedReport.main_findings && (
                  <div className="space-y-2">
                    <h4 className="font-bold text-white text-sm">3. Key Findings</h4>
                    <div className="p-4 rounded-xl bg-[#080c18] border border-slate-800/80 whitespace-pre-wrap">
                      {selectedReport.main_findings}
                    </div>
                  </div>
                )}

                {/* 4. Detailed Analysis */}
                {selectedReport.detailed_analysis && (
                  <div className="space-y-2">
                    <h4 className="font-bold text-white text-sm">4. Detailed Synthesis</h4>
                    <div className="p-4 rounded-xl bg-[#080c18] border border-slate-800/80 whitespace-pre-wrap">
                      {selectedReport.detailed_analysis}
                    </div>
                  </div>
                )}

                {/* 5. Contradictions & Limitations */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {selectedReport.contradictory_findings && (
                    <div className="space-y-2">
                      <h4 className="font-bold text-amber-400 text-xs uppercase font-mono">
                        5. Divergent Claims & Contradictions
                      </h4>
                      <p className="p-3.5 rounded-xl bg-amber-500/5 border border-amber-500/20 text-xs">
                        {selectedReport.contradictory_findings}
                      </p>
                    </div>
                  )}

                  {selectedReport.limitations && (
                    <div className="space-y-2">
                      <h4 className="font-bold text-slate-400 text-xs uppercase font-mono">
                        6. Limitations & Caveats
                      </h4>
                      <p className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
                        {selectedReport.limitations}
                      </p>
                    </div>
                  )}
                </div>

                {/* 7. Unanswered Questions */}
                {selectedReport.unanswered_questions && (
                  <div className="space-y-2">
                    <h4 className="font-bold text-white text-sm">7. Unanswered Questions</h4>
                    <div className="p-4 rounded-xl bg-[#080c18] border border-slate-800/80 whitespace-pre-wrap">
                      {selectedReport.unanswered_questions}
                    </div>
                  </div>
                )}

                {/* 8. Conclusion */}
                {selectedReport.conclusion && (
                  <div className="space-y-2">
                    <h4 className="font-bold text-white text-sm">8. Conclusion</h4>
                    <p className="p-4 rounded-xl bg-[#080c18] border border-slate-800/80">
                      {selectedReport.conclusion}
                    </p>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="h-full flex items-center justify-center text-center text-xs text-slate-500">
              Select or generate a research report to view its structured analysis.
            </div>
          )}
        </Card>
      </div>

      {/* Generator Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Generate Research Report">
        <form onSubmit={handleGenerate} className="space-y-4">
          <Input
            label="Research Question"
            placeholder="e.g. How does self-supervised learning compare with contrastive learning in visual representation?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            required
          />

          <Input
            label="Custom Report Title (Optional)"
            placeholder="e.g. Comparative Analysis of Vision Representation Learning"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />

          <Input
            label="Focus Areas / Topics (Comma-separated)"
            placeholder="e.g. Sample efficiency, Compute benchmarks, Downstream accuracy"
            value={focusAreas}
            onChange={(e) => setFocusAreas(e.target.value)}
          />

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <Button type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={isGenerating}>
              Run Report Synthesis
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
