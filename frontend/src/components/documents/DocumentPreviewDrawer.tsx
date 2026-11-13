import React, { useEffect, useState } from 'react';
import { X, FileText, Sparkles, Layers, BookOpen, Clock } from 'lucide-react';
import { DocumentPreview } from '../../types';
import { Badge } from '../common/Badge';
import { api } from '../../api/client';

interface DocumentPreviewDrawerProps {
  documentId: string | null;
  onClose: () => void;
}

export const DocumentPreviewDrawer: React.FC<DocumentPreviewDrawerProps> = ({
  documentId,
  onClose,
}) => {
  const [data, setData] = useState<DocumentPreview | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    if (!documentId) return;
    const fetchPreview = async () => {
      setIsLoading(true);
      try {
        const preview = await api.getDocumentPreview(documentId);
        setData(preview);
      } catch (e) {
        console.error(e);
      } finally {
        setIsLoading(false);
      }
    };
    fetchPreview();
  }, [documentId]);

  if (!documentId) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-xl bg-[#0d1424] border-l border-slate-800 shadow-2xl flex flex-col justify-between animate-in slide-in-from-right duration-200">
      {/* Header */}
      <div className="p-6 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="p-2 rounded-xl bg-slate-800 border border-slate-700 text-brand-400">
            <FileText className="w-5 h-5" />
          </div>
          <div className="overflow-hidden">
            <h3 className="font-semibold text-slate-100 text-sm truncate">
              {data?.document.title || 'Loading preview...'}
            </h3>
            <p className="text-xs text-slate-500 font-mono truncate">{data?.document.file_name}</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Body Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {isLoading ? (
          <div className="space-y-4 animate-pulse">
            <div className="h-20 bg-slate-800/50 rounded-xl" />
            <div className="h-40 bg-slate-800/50 rounded-xl" />
          </div>
        ) : data ? (
          <>
            {/* Metadata Pills */}
            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/90 text-center">
                <span className="block text-[11px] text-slate-400 uppercase font-mono">Format</span>
                <span className="text-sm font-semibold text-slate-200 uppercase">
                  {data.document.file_type}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/90 text-center">
                <span className="block text-[11px] text-slate-400 uppercase font-mono">Chunks</span>
                <span className="text-sm font-semibold text-brand-400">
                  {data.document.chunk_count}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/90 text-center">
                <span className="block text-[11px] text-slate-400 uppercase font-mono">Words</span>
                <span className="text-sm font-semibold text-slate-200">
                  {data.document.word_count.toLocaleString()}
                </span>
              </div>
            </div>

            {/* AI Summary Card */}
            {data.document.summary && (
              <div className="p-4 rounded-xl bg-brand-500/5 border border-brand-500/20 space-y-2">
                <div className="flex items-center gap-2 text-brand-400 text-xs font-semibold">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Synthesized Document Summary</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {data.document.summary}
                </p>
              </div>
            )}

            {/* Chunk Inspector */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Indexed Chunks ({data.chunks.length} of {data.total_chunks})
                </h4>
              </div>

              <div className="space-y-2.5">
                {data.chunks.map((chunk) => (
                  <div
                    key={chunk.id}
                    className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs space-y-2 hover:border-slate-700 transition-colors"
                  >
                    <div className="flex items-center justify-between text-[11px] text-slate-500 font-mono">
                      <span>Chunk #{chunk.chunk_index + 1}</span>
                      {chunk.page_number && <span>Page {chunk.page_number}</span>}
                      <span>{chunk.word_count} words</span>
                    </div>
                    <p className="text-slate-300 leading-relaxed font-sans text-xs">
                      {chunk.content}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </>
        ) : null}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-slate-800 flex items-center justify-end">
        <button
          onClick={onClose}
          className="text-xs font-medium text-slate-400 hover:text-slate-200"
        >
          Close Preview
        </button>
      </div>
    </div>
  );
};
