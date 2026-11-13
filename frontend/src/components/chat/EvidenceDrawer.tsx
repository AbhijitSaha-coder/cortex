import React from 'react';
import { X, ExternalLink, Bookmark, FileText } from 'lucide-react';
import { Citation } from '../../types';
import { Badge } from '../common/Badge';

interface EvidenceDrawerProps {
  citation: Citation | null;
  onClose: () => void;
}

export const EvidenceDrawer: React.FC<EvidenceDrawerProps> = ({ citation, onClose }) => {
  if (!citation) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-[#0d1424] border-l border-slate-800 shadow-2xl p-6 flex flex-col justify-between animate-in slide-in-from-right duration-200">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Bookmark className="w-4 h-4 text-brand-400" />
            <h3 className="font-semibold text-slate-100 text-sm">
              Citation Evidence #{citation.citation_index}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Source metadata card */}
        <div className="mt-4 p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
          <div className="flex items-center gap-2 text-slate-300">
            <FileText className="w-4 h-4 text-slate-400" />
            <span className="text-sm font-medium">{citation.document_title}</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            {citation.page_number && <Badge variant="info">Page {citation.page_number}</Badge>}
            {citation.similarity_score !== undefined && (
              <Badge variant="brand">Score: {citation.similarity_score.toFixed(3)}</Badge>
            )}
          </div>
        </div>

        {/* Content Excerpt */}
        <div className="mt-6">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
            Extracted Text Passage
          </h4>
          <div className="p-4 rounded-xl bg-[#080c18] border border-slate-800/80 text-sm leading-relaxed text-slate-200 font-mono text-xs whitespace-pre-wrap selection:bg-brand-500 selection:text-white">
            "{citation.excerpt}"
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
        <span className="text-xs text-slate-500 font-mono">ID: {citation.chunk_id?.slice(0, 8)}...</span>
        <button
          onClick={onClose}
          className="text-xs font-medium text-brand-400 hover:text-brand-300"
        >
          Close Panel
        </button>
      </div>
    </div>
  );
};
