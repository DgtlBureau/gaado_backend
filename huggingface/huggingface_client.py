"""
Hugging Face Inference API Client
Для работы с моделями через Hugging Face Inference API
"""
import os
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

try:
    from huggingface_hub import InferenceClient
except ImportError:
    logger.error("huggingface_hub не установлен. Установите: pip install huggingface_hub")
    InferenceClient = None


# Конфигурация из переменных окружения
HF_API_KEY = os.getenv("HF_API_KEY")
HF_DEFAULT_MODEL = os.getenv("HF_DEFAULT_MODEL", "Qwen/Qwen2.5-7B-Instruct:together")


class HuggingFaceClient:
    """Клиент для работы с Hugging Face Inference API"""
    
    def __init__(self, api_key: Optional[str] = None, default_model: Optional[str] = None):
        """
        Инициализация клиента Hugging Face
        
        Args:
            api_key: API ключ для Hugging Face (если не указан, берется из HF_API_KEY)
            default_model: Модель по умолчанию (если не указана, берется из HF_DEFAULT_MODEL)
        """
        self.api_key = api_key or HF_API_KEY
        self.default_model = default_model or HF_DEFAULT_MODEL
        
        if not self.api_key:
            logger.warning("HF_API_KEY не установлен. Некоторые функции могут не работать.")
            logger.warning("Установите переменную окружения: export HF_API_KEY='your_api_key'")
        
        if InferenceClient is None:
            raise ImportError("huggingface_hub не установлен. Установите: pip install huggingface_hub")
        
        try:
            self.client = InferenceClient(api_key=self.api_key) if self.api_key else None
            logger.info(f"HuggingFace клиент инициализирован. Модель по умолчанию: {self.default_model}")
        except Exception as e:
            logger.error(f"Ошибка инициализации HuggingFace клиента: {e}")
            self.client = None
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Создание chat completion через Hugging Face API
        
        Args:
            messages: Список сообщений в формате [{"role": "user", "content": "..."}]
            model: Имя модели (если не указано, используется default_model)
            temperature: Температура для генерации (0.0-1.0)
            max_tokens: Максимальное количество токенов
            **kwargs: Дополнительные параметры для API
        
        Returns:
            Dict с результатом completion
        """
        if not self.client:
            raise ValueError("HuggingFace клиент не инициализирован. Проверьте HF_API_KEY.")
        
        model = model or self.default_model
        
        try:
            # Подготовка параметров
            params = {}
            if temperature is not None:
                params["temperature"] = temperature
            if max_tokens is not None:
                params["max_tokens"] = max_tokens
            params.update(kwargs)
            
            # Вызов API
            completion = self.client.chat.completions.create(
                model=model,
                messages=messages,
                **params
            )
            
            # Форматирование результата
            result = {
                "model": model,
                "choices": [
                    {
                        "message": {
                            "role": completion.choices[0].message.role,
                            "content": completion.choices[0].message.content
                        },
                        "finish_reason": getattr(completion.choices[0], "finish_reason", None)
                    }
                ],
                "usage": {
                    "prompt_tokens": getattr(completion, "usage", {}).get("prompt_tokens", 0),
                    "completion_tokens": getattr(completion, "usage", {}).get("completion_tokens", 0),
                    "total_tokens": getattr(completion, "usage", {}).get("total_tokens", 0)
                } if hasattr(completion, "usage") else {}
            }
            
            logger.info(f"Chat completion успешно создан. Модель: {model}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при создании chat completion: {e}")
            raise
    
    def simple_chat(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Упрощенный метод для простого чата
        
        Args:
            prompt: Текст запроса пользователя
            model: Имя модели (опционально)
            system_prompt: Системный промпт (опционально)
            **kwargs: Дополнительные параметры
        
        Returns:
            Ответ модели в виде строки
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        result = self.chat_completion(messages=messages, model=model, **kwargs)
        return result["choices"][0]["message"]["content"]
    
    def is_available(self) -> bool:
        """
        Проверка доступности клиента
        
        Returns:
            True если клиент доступен, False иначе
        """
        return self.client is not None and self.api_key is not None

