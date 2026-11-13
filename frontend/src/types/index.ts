export interface User {
  id: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

export interface Document {
  id: string;
  title: string;
  file_name: string;
  file_type: string;
  source_url?: string;
  file_size_bytes: number;
  summary?: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  error_message?: string;
  chunk_count: number;
  word_count: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentChunk {
  id: string;
  document_id: string;
  chunk_index: number;
  content: string;
  word_count: number;
  page_number?: number;
  created_at: string;
}

export interface DocumentPreview {
  document: Document;
  chunks: DocumentChunk[];
  total_chunks: number;
}

export interface Citation {
  id: string;
  chunk_id?: string;
  document_id: string;
  document_title: string;
  citation_index: number;
  excerpt: string;
  page_number?: number;
  similarity_score?: number;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  reasoning_content?: string;
  tokens_used: number;
  created_at: string;
  citations?: Citation[];
}

export interface Conversation {
  id: string;
  title: string;
  model: string;
  created_at: string;
  updated_at: string;
  messages?: Message[];
}

export interface ResearchReport {
  id: string;
  title: string;
  research_question: string;
  executive_summary?: string;
  main_findings?: string;
  detailed_analysis?: string;
  contradictory_findings?: string;
  limitations?: string;
  unanswered_questions?: string;
  conclusion?: string;
  markdown_content: string;
  citations?: Citation[];
  status: string;
  created_at: string;
  updated_at: string;
}

export interface EvaluationSampleResult {
  query: string;
  retrieved_count: number;
  recall: number;
  reciprocal_rank: number;
  relevance_score: number;
  groundedness: number;
  latency_ms: number;
  generated_answer_snippet: string;
}

export interface EvaluationRun {
  id: string;
  dataset_id: string;
  status: string;
  recall_at_k: number;
  mrr: number;
  relevance_score: number;
  citation_precision: number;
  groundedness_score: number;
  avg_latency_ms: number;
  total_tokens: number;
  estimated_cost_usd: number;
  sample_count: number;
  results?: EvaluationSampleResult[];
  created_at: string;
}

export interface DashboardStats {
  total_documents: number;
  processed_documents: number;
  failed_documents: number;
  total_chunks: number;
  total_conversations: number;
  total_reports: number;
  storage_bytes: number;
  recent_activity: Array<{
    id: string;
    type: string;
    title: string;
    timestamp: string;
    status: string;
    extra: string;
  }>;
}

export interface UsageSummary {
  total_requests: number;
  total_tokens: number;
  estimated_cost_usd: number;
  usage_by_type: Record<string, number>;
  recent_usage: Array<{
    id: string;
    request_type: string;
    total_tokens: number;
    estimated_cost: number;
    model_name: string;
    created_at: string;
  }>;
}

