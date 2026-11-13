import json
import re
from typing import List, Generator
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.conversation import Conversation, Message, MessageCitation
from app.models.document import Document
from app.models.evaluation import UsageRecord
from app.schemas.chat import ChatMessageRequest, MessageResponse, CitationResponse
from app.services.retrieval.hybrid_search import HybridSearchEngine
from app.services.ai.providers import get_llm_provider
from app.services.ai.guardrails import format_evidence_context, SYSTEM_RESEARCH_PROMPT
from app.services.ai.context import context_manager
from app.services.agent.engine import AgentExecutionEngine
from app.core.logging import logger

router = APIRouter(prefix="/chat", tags=["AI Research"])


@router.post("", response_model=MessageResponse)
def send_chat_message(
    payload: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Core conversational research endpoint. Supports both grounded RAG and autonomous Agentic mode.
    """
    # 1. Resolve or create conversation
    if payload.conversation_id:
        conv = (
            db.query(Conversation)
            .filter(Conversation.id == payload.conversation_id, Conversation.user_id == current_user.id)
            .first()
        )
        if not conv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    else:
        conv_title = payload.message[:40] + ("..." if len(payload.message) > 40 else "")
        conv = Conversation(
            user_id=current_user.id,
            title=conv_title,
            model="default",
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)

    # 2. Save user message
    user_msg = Message(
        conversation_id=conv.id,
        user_id=current_user.id,
        role="user",
        content=payload.message,
    )
    db.add(user_msg)
    db.commit()

    # 3. Handle according to mode
    if payload.mode == "agent":
        agent_engine = AgentExecutionEngine(db, current_user.id)
        agent_res = agent_engine.run(
            query=payload.message,
            conversation_id=conv.id,
            message_id=user_msg.id,
        )
        answer_text = agent_res["answer"]
        reasoning = json.dumps(agent_res.get("tool_executions", []))
        tokens_info = agent_res.get("tokens", {})

        assistant_msg = Message(
            conversation_id=conv.id,
            user_id=current_user.id,
            role="assistant",
            content=answer_text,
            reasoning_content=reasoning,
            tokens_used=tokens_info.get("total_tokens", 0),
        )
        db.add(assistant_msg)
        db.commit()
        db.refresh(assistant_msg)

        return MessageResponse(
            id=assistant_msg.id,
            conversation_id=conv.id,
            role="assistant",
            content=assistant_msg.content,
            reasoning_content=assistant_msg.reasoning_content,
            tokens_used=assistant_msg.tokens_used,
            created_at=assistant_msg.created_at,
            citations=[],
        )

    else:
        # Standard Grounded RAG mode
        hybrid_engine = HybridSearchEngine(db)
        search_res = hybrid_engine.search(
            query=payload.message,
            user_id=current_user.id,
            mode="hybrid",
            top_k=5,
            document_ids=payload.document_ids,
            rerank=True,
        )
        evidence_items = search_res["results"]
        evidence_context = format_evidence_context(evidence_items)

        # Retrieve prior conversation turns
        prior_messages = (
            db.query(Message)
            .filter(Message.conversation_id == conv.id, Message.id != user_msg.id)
            .order_by(Message.created_at.asc())
            .all()
        )
        history_list = [{"role": m.role, "content": m.content} for m in prior_messages]

        prepared_messages = context_manager.prepare_messages(
            conversation_history=history_list,
            current_query=payload.message,
            evidence_context=evidence_context,
        )

        llm = get_llm_provider()
        llm_res = llm.generate(
            messages=prepared_messages,
            system_prompt=SYSTEM_RESEARCH_PROMPT,
            temperature=0.2,
            max_tokens=1500,
        )

        assistant_msg = Message(
            conversation_id=conv.id,
            user_id=current_user.id,
            role="assistant",
            content=llm_res.get("content", ""),
            tokens_used=llm_res.get("total_tokens", 0),
        )
        db.add(assistant_msg)
        db.commit()
        db.refresh(assistant_msg)

        # Create Citation records from retrieved evidence
        citations_resp = []
        for i, item in enumerate(evidence_items, 1):
            citation_marker = f"[Citation {i}]"
            # Link citation if mentioned or if it was top evidence
            if citation_marker in assistant_msg.content or i <= 2:
                cit_record = MessageCitation(
                    message_id=assistant_msg.id,
                    chunk_id=item["chunk_id"],
                    document_id=item["document_id"],
                    citation_index=i,
                    excerpt=item["content"][:200],
                    page_number=item["page_number"],
                    similarity_score=item["score"],
                )
                db.add(cit_record)
                citations_resp.append(
                    CitationResponse(
                        id=cit_record.id,
                        chunk_id=item["chunk_id"],
                        document_id=item["document_id"],
                        document_title=item["document_title"],
                        citation_index=i,
                        excerpt=item["content"][:200],
                        page_number=item["page_number"],
                        similarity_score=item["score"],
                    )
                )

        # Log usage
        usage = UsageRecord(
            user_id=current_user.id,
            request_type="chat",
            prompt_tokens=llm_res.get("prompt_tokens", 0),
            completion_tokens=llm_res.get("completion_tokens", 0),
            total_tokens=llm_res.get("total_tokens", 0),
            estimated_cost=0.0005,
            model_name="cortex-rag-v1",
        )
        db.add(usage)
        db.commit()

        return MessageResponse(
            id=assistant_msg.id,
            conversation_id=conv.id,
            role="assistant",
            content=assistant_msg.content,
            tokens_used=assistant_msg.tokens_used,
            created_at=assistant_msg.created_at,
            citations=citations_resp,
        )


@router.post("/stream")
def stream_chat_message(
    payload: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Streaming SSE endpoint delivering incremental tokens and structured citation payloads.
    """
    # Resolve or create conversation
    if payload.conversation_id:
        conv = (
            db.query(Conversation)
            .filter(Conversation.id == payload.conversation_id, Conversation.user_id == current_user.id)
            .first()
        )
        if not conv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    else:
        conv = Conversation(
            user_id=current_user.id,
            title=payload.message[:40] + ("..." if len(payload.message) > 40 else ""),
            model="default",
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)

    # Save user message
    user_msg = Message(
        conversation_id=conv.id,
        user_id=current_user.id,
        role="user",
        content=payload.message,
    )
    db.add(user_msg)
    db.commit()

    # Retrieve evidence
    hybrid_engine = HybridSearchEngine(db)
    search_res = hybrid_engine.search(
        query=payload.message,
        user_id=current_user.id,
        mode="hybrid",
        top_k=5,
        document_ids=payload.document_ids,
        rerank=True,
    )
    evidence_items = search_res["results"]
    evidence_context = format_evidence_context(evidence_items)

    prior_messages = (
        db.query(Message)
        .filter(Message.conversation_id == conv.id, Message.id != user_msg.id)
        .order_by(Message.created_at.asc())
        .all()
    )
    history_list = [{"role": m.role, "content": m.content} for m in prior_messages]

    prepared_messages = context_manager.prepare_messages(
        conversation_history=history_list,
        current_query=payload.message,
        evidence_context=evidence_context,
    )

    llm = get_llm_provider()

    def event_generator() -> Generator[str, None, None]:
        full_text = []
        try:
            # Yield metadata event
            meta_event = {
                "type": "metadata",
                "conversation_id": conv.id,
                "evidence_count": len(evidence_items),
            }
            yield f"data: {json.dumps(meta_event)}\n\n"

            for token in llm.generate_stream(prepared_messages, SYSTEM_RESEARCH_PROMPT, temperature=0.2):
                full_text.append(token)
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            final_content = "".join(full_text)

            # Save assistant message to DB
            saved_msg = Message(
                conversation_id=conv.id,
                user_id=current_user.id,
                role="assistant",
                content=final_content,
                tokens_used=len(final_content.split()),
            )
            db.add(saved_msg)
            db.commit()
            db.refresh(saved_msg)

            # Build citations
            citations_list = []
            for i, item in enumerate(evidence_items, 1):
                cit = MessageCitation(
                    message_id=saved_msg.id,
                    chunk_id=item["chunk_id"],
                    document_id=item["document_id"],
                    citation_index=i,
                    excerpt=item["content"][:200],
                    page_number=item["page_number"],
                    similarity_score=item["score"],
                )
                db.add(cit)
                citations_list.append({
                    "id": cit.id,
                    "citation_index": i,
                    "document_id": item["document_id"],
                    "document_title": item["document_title"],
                    "excerpt": item["content"][:200],
                    "page_number": item["page_number"],
                    "similarity_score": item["score"],
                })
            db.commit()

            done_event = {
                "type": "done",
                "message_id": saved_msg.id,
                "citations": citations_list,
            }
            yield f"data: {json.dumps(done_event)}\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            err_event = {"type": "error", "error": str(e)}
            yield f"data: {json.dumps(err_event)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

