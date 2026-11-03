
from typing import List, Dict, Any, Optional
from sqlmodel import Session

from app.crud.crud_vector import VectorRepository
from app.crud.crud_user import get_users, get_user_history
from app.services.song_service import SongService


class UserVectorService:
    """
    處理用戶向量相關的業務邏輯，包括推薦歌曲。
    """

    def __init__(self, db: Session):
        self.vector_repository = VectorRepository()
        self.db = db

    async def get_recommended_songs(
        self,
        user_id: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        根據用戶 ID 獲取推薦歌曲列表。
        """
        if limit <= 0:
            raise ValueError("Limit must be a positive integer.")

        # 1. 查詢用戶向量
        user_vector = await (
            self.vector_repository.search_vector_by_user_id(user_id)
        )

        if user_vector is None:
            raise ValueError(
                f"No vector found for user ID: {user_id}. "
                "Cannot generate recommendations."
            )

        # 2. 搜尋相似用戶
        # 多找一個，排除自己
        similar_users = await self._find_similar_users(
            user_id,
            user_vector,
            limit + 1
        )
        print("相似使用者數量：", len(similar_users), flush=True)
        

        # 3. 從相似用戶的聆聽紀錄中取得推薦歌曲
        recommended_song_ids = await (
            self._get_recommendations_from_similar_users(
                user_id,
                similar_users
            )
        )
        print("候選推薦歌曲數量：", len(recommended_song_ids), flush=True)
        print("前 5 個歌曲 ID：", recommended_song_ids[:5], flush=True)

        # 根據 limit 參數限制推薦歌曲 ID
        recommended_song_ids = recommended_song_ids[:limit]

        # 獲取推薦歌曲的詳細資訊
        recommended_songs_details = []

        print("成功取得歌曲詳細資料：", len(recommended_songs_details), flush=True)

        for song_id in recommended_song_ids:
            song_details = await self._fetch_song_details(song_id)

            if song_details:
                recommended_songs_details.append(song_details)

        return recommended_songs_details
    

    async def _find_similar_users(
        self,
        user_id: str,
        user_vector: List[float],
        limit: int
    ) -> List[str]:
        """
        內部方法：在 Qdrant 中搜尋與指定向量相似的用戶。
        """
        search_result = await (
            self.vector_repository.search_similar_users(
                user_vector,
                limit
            )
        )

        # 從 Point 中提取 original_id（用戶 ID）
        similar_users = [
            point.payload["original_id"]
            for point in search_result
            if point.payload
            and "original_id" in point.payload
            and point.payload["original_id"] != user_id
        ]

        if not similar_users:
            return []

        return similar_users

   
    
    async def _get_recommendations_from_similar_users(
        self,
        user_id: str,
        similar_user_ids: List[str]
    ) -> List[str]:

    # 取得目前使用者聽過的歌曲
        user_history_songs = set(
            get_user_history(self.db, user_id)
        )

        print("目前使用者聽過的歌曲：", user_history_songs, flush=True)

        recommended_songs = set()

        for similar_user_id in similar_user_ids:

        # 取得相似使用者聽過的歌曲
            similar_user_history_songs = set(
                get_user_history(self.db, similar_user_id)
            )

            print(
                f"相似使用者 {similar_user_id} "
                f"聽過的歌曲：{similar_user_history_songs}",
                flush=True
            )

        # 排除目前使用者已經聽過的歌曲
            new_recommendations = (
                similar_user_history_songs - user_history_songs
            )

            print(
                f"新增候選歌曲：{new_recommendations}",
                flush=True
            )

            recommended_songs.update(new_recommendations)

        print(
            f"候選推薦歌曲總數：{len(recommended_songs)}",
            flush=True
        )

        return list(recommended_songs)



    async def _fetch_song_details(
        self,
        song_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        內部方法：從 PostgreSQL 獲取歌曲的詳細資訊。
        """
        song_service = SongService(self.db)
        song_details = song_service.get_song(song_id)

        if not song_details:
            print(
                f"Warning: Song with ID {song_id} not found in DB."
            )
            return None

        return song_details

    async def get_users(
        self,
        skip: int = 0,
        limit: int = 10
    ) -> List[str]:
        """
        獲取所有用戶的列表。

        :param limit: 返回的用戶數量限制。
        :return: 用戶列表。
        """
        if limit <= 0:
            raise ValueError("Limit must be a positive integer.")

        try:
            return get_users(self.db, skip=skip, limit=limit)

        except Exception as e:
            raise RuntimeError(
                f"An error occurred while fetching users: {e}"
            ) from e
