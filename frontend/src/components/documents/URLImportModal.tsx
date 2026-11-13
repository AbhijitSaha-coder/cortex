import React, { useState } from 'react';
import { Globe, ShieldCheck, AlertCircle } from 'lucide-react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { api } from '../../api/client';

interface URLImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImported: () => void;
}

export const URLImportModal: React.FC<URLImportModalProps> = ({ isOpen, onClose, onImported }) => {
  const [url, setUrl] = useState<string>('');
  const [title, setTitle] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleImport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    setIsLoading(true);
    setError(null);
    try {
      await api.importUrl(url.trim(), title.trim() || undefined);
      setUrl('');
      setTitle('');
      onImported();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to import web content');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Import Web URL">
      <form onSubmit={handleImport} className="space-y-4">
        <Input
          label="Web Page URL"
          placeholder="https://example.com/research-paper"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          required
          leftIcon={<Globe className="w-4 h-4" />}
        />

        <Input
          label="Custom Document Title (Optional)"
          placeholder="Leave blank to use web page title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />

        <div className="flex items-start gap-2.5 p-3 rounded-xl bg-blue-500/10 border border-blue-500/20 text-xs text-blue-300">
          <ShieldCheck className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
          <span>
            <strong>SSRF Protected:</strong> Private IP ranges, loopback addresses, internal services, and cloud metadata endpoints are strictly blocked.
          </span>
        </div>

        {error && (
          <div className="flex items-center gap-2 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-xs text-red-400">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
          <Button type="button" variant="ghost" onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" isLoading={isLoading} disabled={!url.trim()}>
            Crawl & Ingest
          </Button>
        </div>
      </form>
    </Modal>
  );
};
