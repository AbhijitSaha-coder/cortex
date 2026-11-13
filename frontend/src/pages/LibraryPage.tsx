import React, { useEffect, useState } from 'react';
import {
  FileText,
  Search,
  UploadCloud,
  Globe,
  Trash2,
  Eye,
  Filter,
  CheckCircle2,
  Clock,
  AlertCircle,
  ExternalLink,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Input } from '../components/common/Input';
import { Document } from '../types';
import { api } from '../api/client';
import { UploadModal } from '../components/documents/UploadModal';
import { URLImportModal } from '../components/documents/URLImportModal';
import { DocumentPreviewDrawer } from '../components/documents/DocumentPreviewDrawer';

export const LibraryPage: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  
  const [isUploadOpen, setIsUploadOpen] = useState<boolean>(false);
  const [isUrlOpen, setIsUrlOpen] = useState<boolean>(false);
  const [previewDocId, setPreviewDocId] = useState<string | null>(null);

  const fetchDocs = async () => {
    try {
      const data = await api.listDocuments({
        search: search || undefined,
        file_type: typeFilter || undefined,
        status: statusFilter || undefined,
      });
      setDocuments(data);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, [typeFilter, statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchDocs();
  };

  const handleDelete = async (id: string, title: string) => {
    if (!window.confirm(`Delete document "${title}" and all associated vectors?`)) return;
    try {
      await api.deleteDocument(id);
      setDocuments(documents.filter((d) => d.id !== id));
    } catch (e) {
      alert('Failed to delete document');
    }
  };

  const renderStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant="success">Completed</Badge>;
      case 'processing':
        return <Badge variant="warning">Processing</Badge>;
      case 'queued':
        return <Badge variant="info">Queued</Badge>;
      case 'failed':
        return <Badge variant="danger">Failed</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Knowledge Library</h1>
          <p className="text-xs text-slate-400 mt-1">
            Manage your research papers, articles, and vectorized knowledge corpus
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

      {/* Search & Filters */}
      <div className="flex flex-col md:flex-row gap-3">
        <form onSubmit={handleSearchSubmit} className="flex-1">
          <Input
            placeholder="Search documents by title..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            leftIcon={<Search className="w-4 h-4" />}
          />
        </form>

        <div className="flex items-center gap-3">
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-brand-500"
          >
            <option value="">All Formats</option>
            <option value="pdf">PDF Documents</option>
            <option value="txt">Plain Text</option>
            <option value="md">Markdown</option>
            <option value="url">Web URLs</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-brand-500"
          >
            <option value="">All Statuses</option>
            <option value="completed">Completed</option>
            <option value="processing">Processing</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      {/* Documents Table */}
      <Card className="p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0b101e] border-b border-slate-800 text-slate-400 font-mono uppercase text-[11px]">
              <tr>
                <th className="py-3 px-4">Document Title</th>
                <th className="py-3 px-4">Format</th>
                <th className="py-3 px-4">Chunks</th>
                <th className="py-3 px-4">Word Count</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Added</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-500">
                    Loading documents...
                  </td>
                </tr>
              ) : documents.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-500">
                    No documents found matching your filter.
                  </td>
                </tr>
              ) : (
                documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4 font-medium text-slate-200 max-w-xs truncate">
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-brand-400 flex-shrink-0" />
                        <span className="truncate" title={doc.title}>
                          {doc.title}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className="uppercase font-mono text-[11px] text-slate-400">
                        {doc.file_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">
                      {doc.chunk_count}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-400">
                      {doc.word_count.toLocaleString()}
                    </td>
                    <td className="py-3 px-4">
                      {renderStatusBadge(doc.status)}
                    </td>
                    <td className="py-3 px-4 text-slate-500 font-mono text-[11px]">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-right space-x-1">
                      <button
                        onClick={() => setPreviewDocId(doc.id)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-brand-400 hover:bg-slate-800 transition-colors"
                        title="Inspect Chunks and Summary"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(doc.id, doc.title)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                        title="Delete Document"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploaded={fetchDocs}
      />
      <URLImportModal
        isOpen={isUrlOpen}
        onClose={() => setIsUrlOpen(false)}
        onImported={fetchDocs}
      />
      <DocumentPreviewDrawer
        documentId={previewDocId}
        onClose={() => setPreviewDocId(null)}
      />
    </div>
  );
};

