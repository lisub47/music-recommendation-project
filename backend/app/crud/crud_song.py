
from typing import List, Optional
from sqlmodel import Session, select
from app.model import Song, Artist
from sqlalchemy.orm import selectinload


def get_songs(db: Session, skip: int = 0, limit: int = 100) -> List[tuple[Song, str]]:
    """
    從資料庫中提取所有歌曲，支援分頁功能。

    :param db: 資料庫會話
    :param skip: 跳過的記錄數
    :param limit: 返回的記錄數上限
    :return: 歌曲列表
    """
    statement = (
        select(Song, Artist.artist_name)
        .join(Artist, Song.artist_id == Artist.artist_id)
        .offset(skip)
        .limit(limit)
    )

    songs = db.exec(statement).all()
    return songs


def get_song(db: Session, song_id: str) -> Optional[tuple[Song, str]]:
    """
    根據歌曲 ID 獲取特定歌曲。

    :param db: 資料庫會話
    :param song_id: 要查詢的歌曲 ID
    :return: 歌曲詳細資料或 None（如果未找到）
    """
    statement = (
        select(Song, Artist.artist_name)
        .join(Artist, Song.artist_id == Artist.artist_id)
        .where(Song.song_id == song_id)
    )

    result = db.exec(statement).first()

    return result
