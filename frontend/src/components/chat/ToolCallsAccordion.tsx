import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Terminal, CheckCircle2, Clock } from 'lucide-react';

interface ToolExecution {
  iteration: number;
  tool_name: string;
  arguments: Record<string, any>;
  status: string;
  execution_time_ms: number;
}

interface ToolCallsAccordionProps {
  reasoningJson?: string;
}

export const ToolCallsAccordion: React.FC<ToolCallsAccordionProps> = ({ reasoningJson }) => {
  const [isOpen, setIsOpen] = useState<boolean>(false);

  if (!reasoningJson) return null;

  let toolExecutions: ToolExecution[] = [];
  try {
    toolExecutions = JSON.parse(reasoningJson);
  } catch (e) {
    return null;
  }

  if (!Array.isArray(toolExecutions) || toolExecutions.length === 0) return null;

  return (
    <div className="my-2 border border-slate-800/90 rounded-xl overflow-hidden bg-slate-900/50 text-xs">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-3.5 py-2 hover:bg-slate-800/40 text-slate-400 hover:text-slate-200 transition-colors"
      >
        <div className="flex items-center gap-2 font-mono">
          <Terminal className="w-3.5 h-3.5 text-brand-400" />
          <span>Agent Reasoning & Tool Calls ({toolExecutions.length} actions)</span>
        </div>
        {isOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
      </button>

      {isOpen && (
        <div className="p-3 border-t border-slate-800/80 space-y-2 bg-[#080c18]">
          {toolExecutions.map((exec, idx) => (
            <div key={idx} className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 font-mono text-[11px] space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-brand-400 font-semibold">
                  #{exec.iteration} call: {exec.tool_name}
                </span>
                <span className="flex items-center gap-1 text-slate-500 text-[10px]">
                  <Clock className="w-3 h-3" /> {exec.execution_time_ms}ms
                </span>
              </div>
              <div className="text-slate-400 overflow-x-auto">
                <span className="text-slate-500">args:</span> {JSON.stringify(exec.arguments)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

