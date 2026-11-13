import json
import re
import time
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.agent import AgentToolExecution
from app.services.agent.tools import AgentToolRegistry
from app.services.ai.providers import get_llm_provider
from app.services.ai.guardrails import sanitize_untrusted_text, SYSTEM_RESEARCH_PROMPT
from app.core.logging import logger


class AgentExecutionEngine:
    """
    Controlled agent execution loop.
    Enforces maximum tool iterations, parameter validation, timeout boundaries,
    and prompt-injection defenses.
    """

    def __init__(self, db: Session, user_id: str, max_iterations: int = 5):
        self.db = db
        self.user_id = user_id
        self.max_iterations = max_iterations
        self.registry = AgentToolRegistry(db, user_id)
        self.llm = get_llm_provider()

    def _build_agent_system_prompt(self) -> str:
        tools_json = json.dumps(self.registry.get_tool_definitions(), indent=2)
        return f"""{SYSTEM_RESEARCH_PROMPT}

You are equipped with autonomous research tools. To execute a tool, output a JSON tool call inside <tool_call></tool_call> tags:
<tool_call>
{{"name": "tool_name", "arguments": {{"param": "value"}}}}
</tool_call>

Available Tools:
{tools_json}

RULES:
1. When a user asks a complex research question, analyze what information is required.
2. Call tools to search, inspect chunks, summarize, compare documents, or identify gaps.
3. Once you have acquired sufficient evidence, respond directly with your comprehensive final answer. Do NOT call more tools.
4. Always cite your findings using [Citation X] corresponding to the retrieved evidence.
5. You have a maximum of {self.max_iterations} tool actions.
"""

    def run(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        message_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Runs the controlled agent loop."""
        start_time = time.time()
        tool_executions_log = []
        messages = [{"role": "user", "content": f"Research Task: {query}"}]
        system_prompt = self._build_agent_system_prompt()

        final_content = ""
        total_prompt_tokens = 0
        total_completion_tokens = 0

        for iteration in range(self.max_iterations):
            logger.info(f"[Agent Loop] Iteration {iteration + 1} for query: {query[:50]}")
            llm_res = self.llm.generate(
                messages=messages,
                system_prompt=system_prompt,
                temperature=0.2,
                max_tokens=1500,
            )
            content = llm_res.get("content", "")
            total_prompt_tokens += llm_res.get("prompt_tokens", 0)
            total_completion_tokens += llm_res.get("completion_tokens", 0)

            # Check for tool call
            tool_match = re.search(r"<tool_call>(.*?)</tool_call>", content, re.DOTALL)
            if not tool_match:
                # No tool call; final answer produced
                final_content = content
                break

            # Parse and execute tool
            call_raw = tool_match.group(1).strip()
            tool_name = "unknown"
            tool_args = {}
            try:
                call_data = json.loads(call_raw)
                tool_name = call_data.get("name", "")
                tool_args = call_data.get("arguments", {})
            except Exception as e:
                logger.warning(f"Failed to parse tool JSON: {call_raw} ({e})")
                tool_result_str = f"Error: Invalid tool call JSON format: {str(e)}"
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": f"<tool_result error='json_parse'>{tool_result_str}</tool_result>"})
                continue

            # Execute tool
            exec_res = self.registry.execute(tool_name, tool_args)
            exec_time = exec_res.get("elapsed_ms", 0)
            status = exec_res.get("status", "success")
            result_payload = exec_res.get("result", {})
            error_msg = exec_res.get("error")

            # Persist execution log in DB
            db_log = AgentToolExecution(
                conversation_id=conversation_id,
                message_id=message_id,
                user_id=self.user_id,
                tool_name=tool_name,
                tool_input_json=json.dumps(tool_args),
                tool_output_json=json.dumps(result_payload if status == "success" else {"error": error_msg}),
                execution_time_ms=exec_time,
                status=status,
                error=error_msg,
            )
            self.db.add(db_log)
            self.db.commit()

            tool_executions_log.append({
                "iteration": iteration + 1,
                "tool_name": tool_name,
                "arguments": tool_args,
                "status": status,
                "execution_time_ms": exec_time,
            })

            # Append to prompt history
            tool_result_sanitized = sanitize_untrusted_text(json.dumps(result_payload))
            messages.append({"role": "assistant", "content": content})
            messages.append({
                "role": "user",
                "content": f"<tool_result name='{tool_name}' status='{status}'>\n{tool_result_sanitized}\n</tool_result>\nSynthesize the findings or execute next required tool."
            })

        # If loop reached max iterations without concluding, make final generation
        if not final_content:
            messages.append({
                "role": "user",
                "content": "Conclude your research and provide your final synthesized response now."
            })
            final_res = self.llm.generate(messages, system_prompt, temperature=0.2, max_tokens=1500)
            final_content = final_res.get("content", "")
            total_prompt_tokens += final_res.get("prompt_tokens", 0)
            total_completion_tokens += final_res.get("completion_tokens", 0)

        # Strip remaining internal tool call tags from final answer if present
        clean_final = re.sub(r"<tool_call>.*?</tool_call>", "", final_content, flags=re.DOTALL).strip()
        elapsed_total = round((time.time() - start_time) * 1000, 2)

        return {
            "answer": clean_final,
            "tool_executions": tool_executions_log,
            "total_iterations": len(tool_executions_log),
            "execution_time_ms": elapsed_total,
            "tokens": {
                "prompt_tokens": total_prompt_tokens,
                "completion_tokens": total_completion_tokens,
                "total_tokens": total_prompt_tokens + total_completion_tokens,
            }
        }
