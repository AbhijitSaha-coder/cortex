from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.conversation import Conversation, Message, MessageCitation
from app.models.document import Document
from app.schemas.chat import ConversationCreate, ConversationResponse, MessageResponse, CitationResponse

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Creates a new research conversation session."""
    conv = Conversation(
        user_id=current_user.id,
        title=payload.title or "New Research Session",
        model=payload.model or "default",
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@router.get("", response_model=List[ConversationResponse])
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists conversations belonging to the authenticated user."""
    convs = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    return convs


@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves full conversation history with message citations."""
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conv.id)
        .order_by(Message.created_at.asc())
        .all()
    )

    msg_responses = []
    for m in messages:
        citations = (
            db.query(MessageCitation, Document.title)
            .join(Document, MessageCitation.document_id == Document.id)
            .filter(MessageCitation.message_id == m.id)
            .order_by(MessageCitation.citation_index.asc())
            .all()
        )
        cit_objs = [
            CitationResponse(
                id=c.id,
                chunk_id=c.chunk_id,
                document_id=c.document_id,
                document_title=title,
                citation_index=c.citation_index,
                excerpt=c.excerpt,
                page_number=c.page_number,
                similarity_score=c.similarity_score,
            )
            for c, title in citations
        ]
        msg_responses.append(
            MessageResponse(
                id=m.id,
                conversation_id=m.conversation_id,
                role=m.role,
                content=m.content,
                reasoning_content=m.reasoning_content,
                tokens_used=m.tokens_used,
                created_at=m.created_at,
                citations=cit_objs,
            )
        )

    res = ConversationResponse(
        id=conv.id,
        title=conv.title,
        model=conv.model,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=msg_responses,
    )
    return res


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deletes a conversation and its messages."""
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    db.delete(conv)
    db.commit()
    return None
