from typing import List, Dict, Any


class ConversationContextManager:
    """
    Manages conversation history within token bounds.
    Preserves recent context and truncates or summarizes older turns when exceeding limits.
    """

    def __init__(self, max_context_tokens: int = 4000):
        self.max_context_tokens = max_context_tokens

    def estimate_tokens(self, text: str) -> int:
        """Heuristic estimation of tokens (approx 4 characters per token)."""
        if not text:
            return 0
        return max(1, len(text) // 4)

    def prepare_messages(
        self,
        conversation_history: List[Dict[str, str]],
        current_query: str,
        evidence_context: str
    ) -> List[Dict[str, str]]:
        """
        Combines conversation history with the current evidence-augmented user query,
        pruning older messages from the history if total tokens exceed limit.
        """
        current_user_content = f"{evidence_context}\n\nUser Question: {current_query}"
        current_tokens = self.estimate_tokens(current_user_content)

        budget_remaining = max(500, self.max_context_tokens - current_tokens)

        pruned_history: List[Dict[str, str]] = []
        tokens_accumulated = 0

        # Traverse backwards from most recent message
        for msg in reversed(conversation_history):
            msg_tokens = self.estimate_tokens(msg.get("content", ""))
            if tokens_accumulated + msg_tokens <= budget_remaining:
                pruned_history.insert(0, msg)
                tokens_accumulated += msg_tokens
            else:
                break

        messages = pruned_history + [{"role": "user", "content": current_user_content}]
        return messages


context_manager = ConversationContextManager()

