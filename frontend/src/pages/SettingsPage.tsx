import React, { useEffect, useState } from 'react';
import {
  Settings,
  User,
  Key,
  Cpu,
  Moon,
  Sun,
  DollarSign,
  Activity,
  CheckCircle2,
  Save,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Badge } from '../components/common/Badge';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { UsageSummary } from '../types';
import { api } from '../api/client';

export const SettingsPage: React.FC = () => {
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();

  const [fullName, setFullName] = useState<string>(user?.full_name || '');
  const [provider, setProvider] = useState<string>('mock');
  const [openaiKey, setOpenaiKey] = useState<string>('');
  const [geminiKey, setGeminiKey] = useState<string>('');
  const [anthropicKey, setAnthropicKey] = useState<string>('');
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [isSaved, setIsSaved] = useState<boolean>(false);

  useEffect(() => {
    const fetchUsage = async () => {
      try {
        const u = await api.getUsageSummary();
        setUsage(u);
      } catch (e) {
        console.error(e);
      }
    };
    fetchUsage();
  }, []);

  const handleSaveSettings = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 3000);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="pb-6 border-b border-slate-800">
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
          Settings & Configurations
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Configure AI reasoning models, API keys, appearance, and monitor your token budget
        </p>
      </div>

      <form onSubmit={handleSaveSettings} className="space-y-6">
        {/* Profile Card */}
        <Card className="space-y-4">
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <User className="w-4 h-4 text-brand-400" />
            <span>Profile Settings</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Full Name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Dr. Alan Turing"
            />
            <Input
              label="Email Address"
              value={user?.email || ''}
              disabled
              helperText="Managed by account admin"
            />
          </div>
        </Card>

        {/* AI Provider Config */}
        <Card className="space-y-4">
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <Cpu className="w-4 h-4 text-brand-400" />
            <span>AI Reasoning Provider</span>
          </h3>

          <div className="space-y-4 text-xs">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Active LLM Provider
              </label>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3.5 py-2 text-xs text-slate-200 focus:outline-none focus:border-brand-500"
              >
                <option value="mock">Local Deterministic Engine (Offline & Free)</option>
                <option value="openai">OpenAI (GPT-4o / GPT-4o-mini)</option>
                <option value="gemini">Google Gemini (Gemini 1.5 Flash / Pro)</option>
                <option value="anthropic">Anthropic (Claude 3.5 Sonnet)</option>
              </select>
              <p className="text-[11px] text-slate-500 mt-1">
                The local deterministic engine enables 100% offline development, zero-token cost testing, and predictable unit tests.
              </p>
            </div>

            {provider === 'openai' && (
              <Input
                label="OpenAI API Key"
                type="password"
                placeholder="sk-proj-..."
                value={openaiKey}
                onChange={(e) => setOpenaiKey(e.target.value)}
                leftIcon={<Key className="w-4 h-4" />}
              />
            )}

            {provider === 'gemini' && (
              <Input
                label="Google Gemini API Key"
                type="password"
                placeholder="AIzaSy..."
                value={geminiKey}
                onChange={(e) => setGeminiKey(e.target.value)}
                leftIcon={<Key className="w-4 h-4" />}
              />
            )}

            {provider === 'anthropic' && (
              <Input
                label="Anthropic Claude API Key"
                type="password"
                placeholder="sk-ant-..."
                value={anthropicKey}
                onChange={(e) => setAnthropicKey(e.target.value)}
                leftIcon={<Key className="w-4 h-4" />}
              />
            )}
          </div>
        </Card>

        {/* Appearance & Preferences */}
        <Card className="space-y-4">
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <Moon className="w-4 h-4 text-brand-400" />
            <span>Theme & Display</span>
          </h3>

          <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs">
            <div>
              <span className="font-medium text-slate-200 block">Color Theme</span>
              <span className="text-slate-500">Currently active: {theme} mode</span>
            </div>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={toggleTheme}
              icon={theme === 'dark' ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
            >
              Switch to {theme === 'dark' ? 'Light' : 'Dark'}
            </Button>
          </div>
        </Card>

        {/* Usage & Budget Telemetry */}
        <Card className="space-y-4">
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <DollarSign className="w-4 h-4 text-brand-400" />
            <span>Usage & Cost Telemetry</span>
          </h3>

          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[11px] text-slate-500 font-mono block">Total Requests</span>
              <span className="text-base font-bold text-slate-100 font-mono">
                {usage?.total_requests ?? 0}
              </span>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[11px] text-slate-500 font-mono block">Tokens Consumed</span>
              <span className="text-base font-bold text-brand-400 font-mono">
                {(usage?.total_tokens ?? 0).toLocaleString()}
              </span>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[11px] text-slate-500 font-mono block">Estimated Cost</span>
              <span className="text-base font-bold text-emerald-400 font-mono">
                ${(usage?.estimated_cost_usd ?? 0).toFixed(4)}
              </span>
            </div>
          </div>
        </Card>

        {/* Save Bar */}
        <div className="flex items-center justify-between pt-4">
          {isSaved && (
            <span className="flex items-center gap-1.5 text-xs text-brand-400 font-medium">
              <CheckCircle2 className="w-4 h-4" /> Settings updated successfully
            </span>
          )}
          <Button type="submit" variant="primary" className="ml-auto" icon={<Save className="w-4 h-4" />}>
            Save Preferences
          </Button>
        </div>
      </form>
    </div>
  );
};
