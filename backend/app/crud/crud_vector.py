
from typing import List, Optional
from app.core.vector_store import VectorStore
from app.core.config import settings
from qdrant_client import models

class VectorRepository:
    
    def __init__(self):
        vector_store = VectorStore()
        self.vector_client = vector_store.client

    async def search_vector_by_user_id(self, user_id: str) -> Optional[List[float]]:
        """
        根據 user_id 搜尋對應的使用者向量。

        Args:
            user_id: 使用者 ID。

        Returns:
            如果找到，則回傳使用者向量 (List[float])；否則回傳 None。
        """
        try:
        # 使用 scroll API 搜尋
        # 加上 limit=1 因為預期每個 user_id 只有一個向量
            records, _ = self.vector_client.scroll(
                collection_name=settings.COLLECTION_NAME_USER_HISTORY,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="original_id",
                            match=models.MatchValue(value=user_id),
                        ),
                    ],
                ),
                limit=1,
                with_vectors=True
            )

        # 如果找不到任何紀錄，表示該使用者沒有向量
            if not records:
                print(f"找不到 user_id '{user_id}' 的向量。")
                return None

        # 回傳第一個找到的向量
            user_vector = records[0].vector
            return user_vector

        except Exception as e:
            print(f"搜尋 user_id '{user_id}' 的向量時發生錯誤: {e}")
            raise

    
    async def search_similar_users(
        self,
        query_vector: List[float],
        limit: int
    ):
        try:
            results = self.vector_client.query_points(
                collection_name=settings.COLLECTION_NAME_USER_HISTORY,
                query=query_vector,
                limit=limit,
                with_payload=True
            )

            return results.points

        except Exception as e:
            print(f"搜尋相似使用者時發生錯誤: {e}")
            raise

    def cleanup(self):
        self.vector_client.close()










