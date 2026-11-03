
from qdrant_client import QdrantClient
from app.core.config import settings


class VectorStore:
    """
    Qdrant 向量資料庫連接管理類別。
    """

    def __init__(self):
        # 初始化 Qdrant 客戶端，連接到指定 URL
        self.client = QdrantClient(
            url=settings.VECTOR_DATABASE_URL,
        )

    def close(self):
        """
        關閉 Qdrant 客戶端連接。
        """
        if self.client:
            self.client.close()
