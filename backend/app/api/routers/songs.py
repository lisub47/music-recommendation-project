
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List
from app.core.database import get_session
from app.services.song_service import SongService
from app.model import Song


router = APIRouter(
    prefix="/songs",
    tags=["songs"]
)


@router.get("/", response_model=List[dict])
def read_songs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_session)
):
    """
    獲取所有歌曲列表，支援分頁。

    - **skip**: 跳過多少筆記錄。
    - **limit**: 最多返回多少筆記錄。
    """
    service = SongService(db)
    return service.get_songs(skip=skip, limit=limit)


@router.get("/{song_id}", response_model=dict)
def read_song(
    song_id: str,
    db: Session = Depends(get_session)
):
    """
    根據歌曲 ID 獲取特定歌曲。

    - **song_id**: 歌曲的唯一識別 ID。
    """
    service = SongService(db)
    song = service.get_song(song_id)

    if not song:
        # 如果找不到歌曲，返回 404 Not Found 錯誤
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Song not found"
        )

    return song
