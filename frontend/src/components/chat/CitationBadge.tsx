import React from 'react';
import { Bookmark } from 'lucide-react';
import { Citation } from '../../types';

interface CitationBadgeProps {
  citation: Citation;
  onClick: (citation: Citation) => void;
}

export const CitationBadge: React.FC<CitationBadgeProps> = ({ citation, onClick }) => {
  return (
    <button
      onClick={() => onClick(citation)}
      className="inline-flex items-center gap-1 px-2 py-0.5 my-0.5 mx-1 rounded-md text-[11px] font-mono font-medium bg-brand-500/15 hover:bg-brand-500/25 text-brand-300 border border-brand-500/30 transition-all hover:scale-105 active:scale-95 shadow-sm"
      title={`Click to view verified excerpt from ${citation.document_title}`}
    >
      <Bookmark className="w-2.5 h-2.5 text-brand-400" />
      <span>[{citation.citation_index}] {citation.document_title.slice(0, 16)}</span>
    </button>
  );
};

