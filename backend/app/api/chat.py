import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.analysis import ChatMessage
from app.models.user import User
from app.schemas.analysis import ChatRequest, ChatResponse, ChatMessageOut, SourceRef
from app.ai.rag import rag_query

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_msg = ChatMessage(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        company_id=payload.company_id,
        role="user",
        content=payload.question,
        created_at=datetime.utcnow(),
    )
    db.add(user_msg)
    db.commit()

    rag_result = rag_query(
        question=payload.question,
        company_id=payload.company_id,
    )

    answer = rag_result["answer"]
    raw_sources = rag_result.get("sources", [])

    ai_msg = ChatMessage(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        company_id=payload.company_id,
        role="assistant",
        content=answer,
        sources=raw_sources,
        created_at=datetime.utcnow(),
    )
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)

    sources = [
        SourceRef(
            document_name=s.get("document_name", ""),
            page_number=s.get("page_number"),
        )
        for s in raw_sources
    ]

    return ChatResponse(
        answer=answer,
        sources=sources,
        message_id=ai_msg.id,
    )


@router.get("/history", response_model=list[ChatMessageOut])
def chat_history(
    company_id: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(ChatMessage).filter(ChatMessage.user_id == current_user.id)
    if company_id:
        query = query.filter(ChatMessage.company_id == company_id)
    return query.order_by(ChatMessage.created_at.desc()).limit(limit).all()
