import React, { useEffect, useState, useRef } from 'react';
import {
  Send,
  Bot,
  User as UserIcon,
  Plus,
  Trash2,
  Sparkles,
  Zap,
  Bookmark,
  Layers,
  HelpCircle,
  Clock,
  Loader2,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Conversation, Message, Citation } from '../types';
import { api } from '../api/client';
import { EvidenceDrawer } from '../components/chat/EvidenceDrawer';
import { CitationBadge } from '../components/chat/CitationBadge';
import { ToolCallsAccordion } from '../components/chat/ToolCallsAccordion';

export const WorkspacePage: React.FC = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConv, setCurrentConv] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState<string>('');
  const [mode, setMode] = useState<'rag' | 'agent'>('rag');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const suggestedQuestions = [
    'What are the core findings across my uploaded documents?',
    'Compare the methodologies and performance metrics presented.',
    'Identify any contradictory claims or unresolved limitations.',
  ];

  const fetchConversations = async () => {
    try {
      const convs = await api.listConversations();
      setConversations(convs);
      if (convs.length > 0 && !currentConv) {
        selectConversation(convs[0].id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchConversations();
  }, []);

  const selectConversation = async (id: string) => {
    try {
      const conv = await api.getConversation(id);
      setCurrentConv(conv);
      setMessages(conv.messages || []);
    } catch (e) {
      console.error(e);
    }
  };

  const handleNewConversation = () => {
    setCurrentConv(null);
    setMessages([]);
    setInputMessage('');
  };

  const handleDeleteConversation = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.deleteConversation(id);
      setConversations(conversations.filter((c) => c.id !== id));
      if (currentConv?.id === id) {
        handleNewConversation();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = async (queryText?: string) => {
    const textToSend = queryText || inputMessage;
    if (!textToSend.trim() || isLoading) return;

    setInputMessage('');
    setIsLoading(true);

    // Optimistic user message
    const tempUserMsg: Message = {
      id: `temp-${Date.now()}`,
      conversation_id: currentConv?.id || '',
      role: 'user',
      content: textToSend,
      tokens_used: 0,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const response = await api.sendMessage({
        conversation_id: currentConv?.id,
        message: textToSend,
        mode: mode,
      });

      // Update current conversation ID if this was a new session
      if (!currentConv) {
        await fetchConversations();
        selectConversation(response.conversation_id);
      } else {
        setMessages((prev) => [...prev, response]);
      }
    } catch (err: any) {
      const errorMsg: Message = {
        id: `err-${Date.now()}`,
        conversation_id: currentConv?.id || '',
        role: 'assistant',
        content: `Error: ${err.message || 'Failed to complete research request.'}`,
        tokens_used: 0,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] rounded-2xl border border-slate-800 bg-[#0a0f1e] overflow-hidden shadow-2xl">
      {/* Sessions Sidebar */}
      <div className="w-72 bg-[#0c1224] border-r border-slate-800 flex flex-col justify-between hidden md:flex">
        <div className="p-4 border-b border-slate-800">
          <Button
            variant="primary"
            size="sm"
            className="w-full"
            icon={<Plus className="w-4 h-4" />}
            onClick={handleNewConversation}
          >
            New Research Session
          </Button>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          {conversations.map((conv) => {
            const isSelected = currentConv?.id === conv.id;
            return (
              <div
                key={conv.id}
                onClick={() => selectConversation(conv.id)}
                className={`group flex items-center justify-between p-2.5 rounded-xl text-xs cursor-pointer transition-all ${
                  isSelected
                    ? 'bg-slate-800/90 text-brand-300 font-medium border border-slate-700/80 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                }`}
              >
                <div className="truncate flex-1 pr-2">
                  <span className="block truncate">{conv.title}</span>
                  <span className="text-[10px] text-slate-500 font-mono">
                    {new Date(conv.updated_at).toLocaleDateString()}
                  </span>
                </div>
                <button
                  onClick={(e) => handleDeleteConversation(conv.id, e)}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded hover:text-red-400 transition-opacity"
                  title="Delete conversation"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })}
        </div>

        <div className="p-3 border-t border-slate-800 text-[11px] text-slate-500 text-center font-mono">
          <span>{conversations.length} Active Sessions</span>
        </div>
      </div>

      {/* Main Chat Thread */}
      <div className="flex-1 flex flex-col justify-between overflow-hidden bg-[#070b16]">
        {/* Chat Header */}
        <div className="h-16 px-6 border-b border-slate-800 flex items-center justify-between bg-[#0a0f1e]/60 backdrop-blur-md">
          <div className="flex items-center gap-2 overflow-hidden">
            <Bot className="w-5 h-5 text-brand-400 flex-shrink-0" />
            <h2 className="text-sm font-semibold text-slate-200 truncate">
              {currentConv ? currentConv.title : 'New Research Investigation'}
            </h2>
          </div>

          {/* Mode Switcher */}
          <div className="flex items-center gap-1.5 p-1 rounded-xl bg-slate-900 border border-slate-800 text-xs">
            <button
              onClick={() => setMode('rag')}
              className={`px-3 py-1 rounded-lg font-medium transition-all ${
                mode === 'rag'
                  ? 'bg-brand-500/20 text-brand-400 border border-brand-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Grounded RAG
            </button>
            <button
              onClick={() => setMode('agent')}
              className={`px-3 py-1 rounded-lg font-medium transition-all ${
                mode === 'agent'
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Autonomous Agent
            </button>
          </div>
        </div>

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-400">
                <Sparkles className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">How can Cortex help your research?</h3>
                <p className="text-xs text-slate-400 mt-1">
                  Ask multi-document synthesis questions, verify claims, compare papers, or uncover knowledge gaps.
                </p>
              </div>

              {/* Quick suggestions */}
              <div className="w-full space-y-2 pt-2">
                {suggestedQuestions.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendMessage(q)}
                    className="w-full text-left p-3 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-brand-500/50 hover:bg-slate-800/60 text-xs text-slate-300 transition-all font-medium"
                  >
                    "{q}"
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-4 text-xs ${
                  msg.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-400 flex-shrink-0 mt-1">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div
                  className={`max-w-2xl rounded-2xl p-4 space-y-3 ${
                    msg.role === 'user'
                      ? 'bg-brand-600/20 text-slate-100 border border-brand-500/30'
                      : 'bg-slate-900/90 text-slate-200 border border-slate-800/90 shadow-md'
                  }`}
                >
                  {/* Tool execution accordion if present */}
                  {msg.role === 'assistant' && msg.reasoning_content && (
                    <ToolCallsAccordion reasoningJson={msg.reasoning_content} />
                  )}

                  {/* Message body */}
                  <div className="leading-relaxed whitespace-pre-wrap font-sans text-xs">
                    {msg.content}
                  </div>

                  {/* Citations Footer */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="pt-2 border-t border-slate-800/80 mt-2">
                      <span className="text-[10px] uppercase font-mono font-semibold text-slate-500 block mb-1">
                        Verified Sources ({msg.citations.length}):
                      </span>
                      <div className="flex flex-wrap gap-1">
                        {msg.citations.map((c) => (
                          <CitationBadge
                            key={c.id}
                            citation={c}
                            onClick={(cit) => setSelectedCitation(cit)}
                          />
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {msg.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 flex-shrink-0 mt-1">
                    <UserIcon className="w-4 h-4" />
                  </div>
                )}
              </div>
            ))
          )}

          {isLoading && (
            <div className="flex gap-4 items-center text-xs text-slate-400">
              <div className="w-8 h-8 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-400 animate-pulse">
                <Bot className="w-4 h-4" />
              </div>
              <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-brand-400" />
                <span className="font-mono text-xs">
                  {mode === 'agent'
                    ? 'Agent executing tool loop & searching knowledge corpus...'
                    : 'Executing hybrid RRF retrieval & grounding answer...'}
                </span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-slate-800 bg-[#0a0f1e]/70 backdrop-blur-md">
          <div className="relative rounded-2xl bg-slate-900/90 border border-slate-800 focus-within:border-brand-500/80 focus-within:ring-2 focus-within:ring-brand-500/20 transition-all p-2">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question or assign a research task (Shift + Enter for newline)..."
              rows={2}
              className="w-full bg-transparent text-xs text-slate-100 placeholder-slate-500 focus:outline-none resize-none p-2 leading-relaxed font-sans"
            />
            <div className="flex items-center justify-between pt-1 px-2 border-t border-slate-800/40 text-[11px] text-slate-500">
              <span className="font-mono">Mode: {mode === 'agent' ? 'Autonomous Agent' : 'Grounded RAG'}</span>
              <Button
                variant="primary"
                size="sm"
                onClick={() => handleSendMessage()}
                isLoading={isLoading}
                disabled={!inputMessage.trim()}
                icon={<Send className="w-3.5 h-3.5" />}
              >
                Send
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Side Evidence Drawer */}
      <EvidenceDrawer
        citation={selectedCitation}
        onClose={() => setSelectedCitation(null)}
      />
    </div>
  );
};

