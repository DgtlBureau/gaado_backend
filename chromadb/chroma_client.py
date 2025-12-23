"""
ChromaDB client для хранения и поиска векторных представлений документов
"""
import os
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

# Конфигурация из переменных окружения
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "gaado_documents")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Для Cloudflare Workers - используем ChromaDB Cloud или внешний экземпляр
CHROMA_API_URL = os.getenv("CHROMA_API_URL", None)
CHROMA_API_KEY = os.getenv("CHROMA_API_KEY", None)


class ChromaDBClient:
    """Клиент для работы с ChromaDB"""
    
    def __init__(self):
        """Инициализация клиента ChromaDB"""
        self.client = None
        self.collection = None
        self.embedding_model = None
        self._initialize_client()
        self._initialize_embedding_model()
    
    def _initialize_client(self):
        """Инициализация клиента ChromaDB"""
        try:
            if CHROMA_API_URL:
                # Использование ChromaDB Cloud или внешнего экземпляра
                self.client = chromadb.HttpClient(
                    host=CHROMA_API_URL.replace("http://", "").replace("https://", ""),
                    port=CHROMA_PORT,
                    settings=Settings(
                        chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
                        chroma_client_auth_credentials=CHROMA_API_KEY
                    ) if CHROMA_API_KEY else Settings()
                )
            else:
                # Локальный экземпляр ChromaDB
                self.client = chromadb.Client(
                    Settings(
                        chroma_db_impl="duckdb+parquet",
                        persist_directory="./chroma_db"
                    )
                )
            
            # Получаем или создаем коллекцию
            try:
                self.collection = self.client.get_collection(name=CHROMA_COLLECTION_NAME)
                logger.info(f"Использована существующая коллекция: {CHROMA_COLLECTION_NAME}")
            except Exception:
                self.collection = self.client.create_collection(
                    name=CHROMA_COLLECTION_NAME,
                    metadata={"description": "Gaado documents collection"}
                )
                logger.info(f"Создана новая коллекция: {CHROMA_COLLECTION_NAME}")
                
        except Exception as e:
            logger.error(f"Ошибка инициализации ChromaDB: {e}")
            raise
    
    def _initialize_embedding_model(self):
        """Инициализация модели для создания эмбеддингов"""
        try:
            self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
            logger.info(f"Модель эмбеддингов загружена: {EMBEDDING_MODEL}")
        except Exception as e:
            logger.error(f"Ошибка загрузки модели эмбеддингов: {e}")
            raise
    
    def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Добавление документов в ChromaDB
        
        Args:
            texts: Список текстов для добавления
            metadatas: Опциональные метаданные для каждого документа
            ids: Опциональные ID для документов
            
        Returns:
            Список ID добавленных документов
        """
        if not texts:
            raise ValueError("Список текстов не может быть пустым")
        
        # Создание эмбеддингов
        embeddings = self.embedding_model.encode(texts).tolist()
        
        # Генерация ID если не предоставлены
        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in texts]
        
        # Подготовка метаданных
        if metadatas is None:
            metadatas = [{}] * len(texts)
        
        # Добавление в коллекцию
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Добавлено {len(texts)} документов в ChromaDB")
        return ids
    
    def search(
        self,
        query_text: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Поиск похожих документов
        
        Args:
            query_text: Текст запроса
            n_results: Количество результатов для возврата
            filter_metadata: Опциональный фильтр по метаданным
            
        Returns:
            Словарь с результатами поиска
        """
        # Создание эмбеддинга для запроса
        query_embedding = self.embedding_model.encode([query_text]).tolist()[0]
        
        # Поиск в коллекции
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata
        )
        
        # Форматирование результатов
        formatted_results = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    "id": results['ids'][0][i],
                    "document": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results else None
                })
        
        return {
            "query": query_text,
            "results": formatted_results,
            "count": len(formatted_results)
        }
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Получение информации о коллекции"""
        count = self.collection.count()
        return {
            "collection_name": CHROMA_COLLECTION_NAME,
            "document_count": count,
            "embedding_model": EMBEDDING_MODEL
        }
    
    def delete_documents(self, ids: List[str]) -> bool:
        """
        Удаление документов по ID
        
        Args:
            ids: Список ID документов для удаления
            
        Returns:
            True если удаление успешно
        """
        try:
            self.collection.delete(ids=ids)
            logger.info(f"Удалено {len(ids)} документов из ChromaDB")
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления документов: {e}")
            return False


# Глобальный экземпляр клиента
_chroma_client: Optional[ChromaDBClient] = None


def get_chroma_client() -> ChromaDBClient:
    """Получение глобального экземпляра клиента ChromaDB"""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = ChromaDBClient()
    return _chroma_client

