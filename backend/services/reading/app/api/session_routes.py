from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional

from shared.middleware.auth import get_current_user
from ..schemas.reading_schemas import (
    SessionStartRequest,
    SessionEndRequest,
    SessionResponse,
    SessionResultResponse,
    SessionListResponse,
    SessionSyncRequest,
)
from ..services.session_service import SessionService

router = APIRouter()


def get_session_service() -> SessionService:
    return SessionService()


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def start_session(
    data: SessionStartRequest,
    current_user: dict = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
):
    """Start a new reading session"""
    # Check for existing active session
    active = await session_service.get_active_session(current_user.user_id)
    if active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Active session already exists",
        )

    session = await session_service.start_session(
        user_id=current_user.user_id,
        user_book_id=data.user_book_id,
        start_page=data.start_page,
    )
    return session


@router.get("/sessions/active", response_model=Optional[SessionResponse])
async def get_active_session(
    current_user: dict = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
):
    """Get current active reading session"""
    session = await session_service.get_active_session(current_user.user_id)
    return session


@router.post("/sessions/{session_id}/end", response_model=SessionResultResponse)
async def end_session(
    session_id: str,
    data: SessionEndRequest,
    current_user: dict = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
):
    """End a reading session and get results"""
    result = await session_service.end_session(
        session_id=session_id,
        user_id=current_user.user_id,
        end_page=data.end_page,
        focus_score=data.focus_score,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    return result


@router.post("/sessions/{session_id}/pause")
async def pause_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
):
    """Pause a reading session"""
    success = await session_service.pause_session(
        session_id=session_id,
        user_id=current_user.user_id,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    return {"status": "paused"}


@router.post("/sessions/{session_id}/resume")
async def resume_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
):
    """Resume a paused reading session"""
    success = await session_service.resume_session(
        session_id=session_id,
        user_id=current_user.user_id,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    return {"status": "resumed"}


@router.get("/sessions", response_model=SessionListResponse)
async def get_sessions(
    user_book_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
):
    """Get reading session history"""
    return await session_service.get_sessions(
        user_id=current_user.user_id,
        user_book_id=user_book_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )


@router.post("/sessions/sync", response_model=SessionResponse)
async def sync_offline_session(
    data: SessionSyncRequest,
    current_user: dict = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
):
    """Sync an offline reading session"""
    session = await session_service.sync_offline_session(
        user_id=current_user.user_id,
        data=data,
    )
    return session
