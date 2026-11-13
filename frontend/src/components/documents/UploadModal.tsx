import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, CheckCircle2, AlertCircle } from 'lucide-react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { api } from '../../api/client';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploaded: () => void;
}

export const UploadModal: React.FC<UploadModalProps> = ({ isOpen, onClose, onUploaded }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setIsUploading(true);
    setError(null);
    try {
      await api.uploadDocument(selectedFile);
      setSelectedFile(null);
      onUploaded();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Upload Document">
      <div className="space-y-4">
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className="border-2 border-dashed border-slate-700 hover:border-brand-500/80 rounded-2xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-colors bg-slate-900/40 hover:bg-slate-900/70"
        >
          <UploadCloud className="w-10 h-10 text-brand-400 mb-3" />
          <p className="text-sm font-medium text-slate-200">
            {selectedFile ? selectedFile.name : 'Click to browse or drag file here'}
          </p>
          <p className="text-xs text-slate-500 mt-1">
            Supports PDF, TXT, and Markdown files up to 25MB
          </p>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".pdf,.txt,.md,.markdown"
            className="hidden"
          />
        </div>

        {selectedFile && (
          <div className="flex items-center gap-3 p-3 rounded-xl bg-slate-800/60 border border-slate-700/80 text-xs text-slate-300">
            <FileText className="w-4 h-4 text-brand-400" />
            <span className="font-medium truncate">{selectedFile.name}</span>
            <span className="text-slate-500 ml-auto">
              {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
            </span>
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-xs text-red-400">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
          <Button variant="ghost" onClick={onClose} disabled={isUploading}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleUpload}
            isLoading={isUploading}
            disabled={!selectedFile}
          >
            Start Ingestion
          </Button>
        </div>
      </div>
    </Modal>
  );
};
