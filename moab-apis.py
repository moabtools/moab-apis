"""
SerpPro API Client для методов Wordstat
Поддерживает методы: Frequency, Deep, History
"""

from typing import Optional, List
from datetime import datetime
from enum import Enum
import requests
from pydantic import BaseModel, Field


class WordstatDevice(str, Enum):
    """Enum для типов устройств"""
    ALL = "All"
    DESKTOP = "Desktop"
    PHONE = "Phone"
    TABLET = "Tablet"


class WordstatTaskType(str, Enum):
    """Enum для типов задач Wordstat"""
    NONE = "None"
    WS = "Ws"
    QUOTES = "Quotes"
    QUOTES_EXCLAMATION_MARK = "QuotesExclamationMark"
    QUOTES_SQUARE_BRACKETS = "QuotesSquareBrackets"
    QUOTES_EXCLAMATION_MARK_SQUARE_BRACKETS = "QuotesExclamationMarkSquareBrackets"


class WordstatGrouping(str, Enum):
    """Enum для группировки данных"""
    NONE = "None"
    DAY = "Day"
    WEEK = "Week"
    MONTH = "Month"


# Модели данных
class WordstatItemData(BaseModel):
    """Данные элемента Wordstat"""
    frequency: Optional[str] = None
    phrase: Optional[str] = None


class HistoryResponseItem(BaseModel):
    """Элемент истории данных"""
    date: datetime
    frequency: Optional[int] = None
    all_requests_percentage: Optional[float] = None


# Модели запросов
class FrequencyRequest(BaseModel):
    """Запрос частотности"""
    query: Optional[str] = None
    region: Optional[str] = None
    device: WordstatDevice
    task_type: WordstatTaskType


class DeepRequest(BaseModel):
    """Запрос постраничных данных"""
    query: Optional[str] = None
    region: Optional[str] = None
    device: WordstatDevice


class HistoryRequest(BaseModel):
    """Запрос исторических данных"""
    query: Optional[str] = None
    region: Optional[str] = None
    device: WordstatDevice
    grouping: WordstatGrouping


# Модели ответов
class FrequencyResponse(BaseModel):
    """Ответ частотности"""
    query: Optional[str] = None
    date: datetime
    frequency: Optional[int] = None
    is_query_invalid: bool


class DeepResponse(BaseModel):
    """Ответ постраничных данных"""
    query: Optional[str] = None
    date: datetime
    associations: Optional[List[WordstatItemData]] = None
    popular: Optional[List[WordstatItemData]] = None
    is_query_invalid: bool


class HistoryResponse(BaseModel):
    """Ответ исторических данных"""
    query: Optional[str] = None
    date: datetime
    items: Optional[List[HistoryResponseItem]] = None
    is_query_invalid: bool


class SerpProAPIError(Exception):
    """Исключение для ошибок API"""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error {status_code}: {message}")


class SerpProWordstatClient:
    """Клиент для работы с Wordstat API"""
    
    def __init__(self, api_key: str, base_url: str = "https://87.228.42.178:42102/", verify_ssl: bool = False):
        """
        Инициализация клиента
        
        Args:
            api_key: API ключ для авторизации
            base_url: Базовый URL API (по умолчанию https://87.228.42.178:42102/)
            verify_ssl: Проверять SSL сертификаты (по умолчанию True)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.headers.update({
            'X-Api-Key': api_key,
            'Content-Type': 'application/json'
        })
        
        # Отключаем предупреждения о небезопасных запросах, если SSL отключен
        if not verify_ssl:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _make_request(self, method: str, endpoint: str, data: Optional[dict] = None) -> dict:
        """
        Выполняет HTTP запрос к API
        
        Args:
            method: HTTP метод (GET, POST и т.д.)
            endpoint: Конечная точка API
            data: Данные для отправки (для POST запросов)
            
        Returns:
            dict: Ответ от API
            
        Raises:
            SerpProAPIError: При ошибках API
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'POST':
                response = self.session.post(url, json=data, verify=self.verify_ssl)
            else:
                response = self.session.get(url, params=data, verify=self.verify_ssl)
                
            if response.status_code == 200:
                return response.json()
            else:
                error_data = response.json() if response.text else {}
                error_message = error_data.get('title', f'HTTP {response.status_code}')
                raise SerpProAPIError(response.status_code, error_message)
                
        except requests.exceptions.RequestException as e:
            raise SerpProAPIError(0, str(e))

    def get_frequency(self, 
                     query: Optional[str] = None,
                     region: Optional[str] = None, 
                     device: WordstatDevice = WordstatDevice.ALL,
                     task_type: WordstatTaskType = WordstatTaskType.WS) -> FrequencyResponse:
        """
        Получает частотность запроса
        
        Args:
            query: Поисковый запрос
            region: Регион поиска
            device: Тип устройства
            task_type: Тип задачи
            
        Returns:
            FrequencyResponse: Данные о частотности
        """
        request_data = FrequencyRequest(
            query=query,
            region=region,
            device=device,
            task_type=task_type
        )
        
        response_data = self._make_request('POST', '/api/v1/wordstat/frequency', 
                                         request_data.model_dump(exclude_none=True))
        
        return FrequencyResponse(**response_data)

    def get_deep(self,
                query: Optional[str] = None,
                region: Optional[str] = None,
                device: WordstatDevice = WordstatDevice.ALL) -> DeepResponse:
        """
        Получает подробные данные по запросу
        
        Args:
            query: Поисковый запрос
            region: Регион поиска
            device: Тип устройства
            
        Returns:
            DeepResponse: Подробные данные
        """
        request_data = DeepRequest(
            query=query,
            region=region,
            device=device
        )
        
        response_data = self._make_request('POST', '/api/v1/wordstat/deep',
                                         request_data.model_dump(exclude_none=True))
        
        return DeepResponse(**response_data)

    def get_history(self,
                   query: Optional[str] = None,
                   region: Optional[str] = None,
                   device: WordstatDevice = WordstatDevice.ALL,
                   grouping: WordstatGrouping = WordstatGrouping.MONTH) -> HistoryResponse:
        """
        Получает исторические данные по запросу
        
        Args:
            query: Поисковый запрос
            region: Регион поиска
            device: Тип устройства
            grouping: Группировка данных по времени
            
        Returns:
            HistoryResponse: Исторические данные
        """
        request_data = HistoryRequest(
            query=query,
            region=region,
            device=device,
            grouping=grouping
        )
        
        response_data = self._make_request('POST', '/api/v1/wordstat/history',
                                         request_data.model_dump(exclude_none=True))
        
        return HistoryResponse(**response_data)


# Пример использования
if __name__ == "__main__":
    # Инициализация клиента с отключенной проверкой SSL
    # ВНИМАНИЕ: Отключение SSL проверки снижает безопасность!
    # Используйте только в тестовой среде или при работе с самоподписанными сертификатами
    client = SerpProWordstatClient(
        api_key="your-api-key",
        verify_ssl=False  # Отключает проверку SSL сертификатов
    )
    
    # Альтернативно - с включенной проверкой SSL (рекомендуется)
    # client = SerpProWordstatClient(api_key="your-api-key-here", verify_ssl=True)
    
    try:
        # Получение частотности
        frequency_result = client.get_frequency(
            query="Король и Шут",
            region="225",  # Россия
            device=WordstatDevice.ALL,
            task_type=WordstatTaskType.WS
        )
        print("Frequency:", frequency_result.frequency)
        
        # Получение подробных данных
        deep_result = client.get_deep(
            query="Король и Шут",
            region="225",
            device=WordstatDevice.ALL
        )
        print("Deep associations:", len(deep_result.associations or []))
        print("Deep popular:", len(deep_result.popular or []))
        
        # Получение истории
        history_result = client.get_history(
            query="Король и Шут",
            region="225",
            device=WordstatDevice.ALL,
            grouping=WordstatGrouping.MONTH
        )
        print("History items:", len(history_result.items or []))
        
    except SerpProAPIError as e:
        print(f"Ошибка API: {e}")
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")