"""
SerpPro API Client v2 для методов Wordstat, Region и Finance
Основан на новой спецификации API
"""

from typing import Optional, List
from datetime import datetime
from enum import Enum
import time
import requests
from pydantic import BaseModel, Field


# ===== ENUMS =====

class ServiceType(str, Enum):
    """Enum для типов сервисов"""
    WORDSTAT_FREQUENCY = "WordstatFrequency"
    WORDSTAT_DIRECT_FREQUENCY = "WordstatDirectFrequency"
    WORDSTAT_DEEP = "WordstatDeep"
    WORDSTAT_DIRECT_DEEP = "WordstatDirectDeep"
    WORDSTAT_HISTORY = "WordstatHistory"
    YANDEX_SERP_POSITION = "YandexSerpPosition"
    GOOGLE_SERP_POSITION = "GoogleSerpPosition"
    YANDEX_INDEXATION = "YandexIndexation"
    GOOGLE_INDEXATION = "GoogleIndexation"
    YANDEX_SERP_URLS = "YandexSerpUrls"
    GOOGLE_SERP_URLS = "GoogleSerpUrls"


class WordstatDevice(str, Enum):
    """Enum для типов устройств"""
    ALL = "All"
    DESKTOP = "Desktop"
    PHONE = "Phone"
    TABLET = "Tablet"


class WordstatSyntax(str, Enum):
    """Enum для синтаксиса Wordstat"""
    NONE = "None"
    WS = "Ws"
    QUOTES = "Quotes"
    QUOTES_EXCLAMATION_MARK = "QuotesExclamationMark"
    QUOTES_SQUARE_BRACKETS = "QuotesSquareBrackets"
    QUOTES_EXCLAMATION_MARK_SQUARE_BRACKETS = "QuotesExclamationMarkSquareBrackets"


class WordstatTaskType(str, Enum):
    """Enum для типов задач Wordstat"""
    REGULAR = "Regular"
    DIRECT = "Direct"


class WordstatGrouping(str, Enum):
    """Enum для группировки данных"""
    DAY = "Day"
    WEEK = "Week"
    MONTH = "Month"


class SearchSystem(str, Enum):
    """Enum для поисковых систем"""
    YANDEX = "Yandex"
    GOOGLE = "Google"


class RegionSearchType(str, Enum):
    """Enum для типа поиска региона"""
    NAME = "Name"
    CODE = "Code"


# ===== WORDSTAT MODELS =====

class WordstatItemData(BaseModel):
    """Данные элемента Wordstat для Deep"""
    frequency: Optional[str] = None
    phrase: Optional[str] = None


class HistoryResponseItem(BaseModel):
    """Элемент истории данных"""
    date: Optional[str] = None
    frequency: Optional[int] = None
    all_requests_percentage: Optional[float] = None


# ===== REQUEST MODELS =====

class FrequencyRequest(BaseModel):
    """Запрос частотности"""
    query: Optional[str] = None
    region: Optional[str] = None
    device: WordstatDevice = WordstatDevice.ALL
    task_type: WordstatTaskType = WordstatTaskType.REGULAR
    syntax: WordstatSyntax = WordstatSyntax.WS


class DeepRequest(BaseModel):
    """Запрос постраничных данных"""
    query: Optional[str] = None
    region: Optional[str] = None
    device: WordstatDevice = WordstatDevice.ALL
    task_type: WordstatTaskType = WordstatTaskType.REGULAR


class HistoryRequest(BaseModel):
    """Запрос исторических данных"""
    query: str = Field(..., min_length=1, max_length=3000)
    region: Optional[str] = None
    device: WordstatDevice = WordstatDevice.ALL
    grouping: WordstatGrouping = WordstatGrouping.MONTH
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class FinanceStatsRequest(BaseModel):
    """Запрос статистики финансов"""
    service_type: Optional[ServiceType] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


# ===== RESPONSE MODELS =====

class FrequencyResponse(BaseModel):
    """Ответ частотности"""
    frequency: Optional[int] = None


class DeepResponse(BaseModel):
    """Ответ постраничных данных"""
    associations: Optional[List[WordstatItemData]] = None
    popular: Optional[List[WordstatItemData]] = None


class HistoryResponse(BaseModel):
    """Ответ исторических данных"""
    items: Optional[List[HistoryResponseItem]] = None


class RegionResponse(BaseModel):
    """Ответ с данными региона"""
    name: Optional[str] = None
    code: Optional[str] = None


class FinanceStatsResponse(BaseModel):
    """Ответ статистики финансов"""
    request_count: int = 0


class GlobalErrorModel(BaseModel):
    """Модель ошибки"""
    id: Optional[str] = None
    error_message: Optional[str] = None
    instance: Optional[str] = None
    invalid_data: Optional[List[str]] = None


# ===== EXCEPTIONS =====

class SerpProAPIError(Exception):
    """Исключение для ошибок API"""
    def __init__(self, status_code: int, message: str, error_model: Optional[GlobalErrorModel] = None):
        self.status_code = status_code
        self.message = message
        self.error_model = error_model
        super().__init__(f"API Error {status_code}: {message}")


# ===== CLIENT =====

class SerpProClient:
    """Клиент для работы с SerpPro API v2"""

    def __init__(self, api_key: str, base_url: str = "https://moab-apis.ru", verify_ssl: bool = True):
        """
        Инициализация клиента

        Args:
            api_key: API ключ для авторизации
            base_url: Базовый URL API (по умолчанию https://moab-apis.ru)
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

    def _make_request(self, method: str, endpoint: str, data: Optional[dict] = None,
                     params: Optional[dict] = None) -> dict:
        """
        Выполняет HTTP запрос к API с таймаутом 300 секунд и бесконечным циклом повторных попыток

        Args:
            method: HTTP метод (GET, POST и т.д.)
            endpoint: Конечная точка API
            data: Данные для отправки (для POST запросов)
            params: Query параметры (для GET запросов)

        Returns:
            dict: Ответ от API

        Raises:
            SerpProAPIError: При ошибках API (но не при таймауте)
        """
        url = f"{self.base_url}{endpoint}"
        timeout = 300  # Таймаут 300 секунд

        while True:  # Бесконечный цикл повторных попыток
            try:
                if method.upper() == 'POST':
                    response = self.session.post(url, json=data, verify=self.verify_ssl, timeout=timeout)
                else:
                    response = self.session.get(url, params=params, verify=self.verify_ssl, timeout=timeout)

                # Если получен любой HTTP-код ответа, обрабатываем его
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 422:
                    # Обработка ошибки 422 Unprocessable Content (ошибочный запрос)
                    error_data = response.json() if response.text else {}
                    try:
                        error_model = GlobalErrorModel(**error_data)
                        error_message = error_model.error_message or 'Unprocessable Content - invalid query'
                    except:
                        error_message = error_data.get('error_message', 'Unprocessable Content - invalid query')
                        error_model = None
                    raise SerpProAPIError(response.status_code, error_message, error_model)
                else:
                    error_data = response.json() if response.text else {}
                    try:
                        error_model = GlobalErrorModel(**error_data)
                        error_message = error_model.error_message or f'HTTP {response.status_code}'
                    except:
                        error_message = error_data.get('error_message', f'HTTP {response.status_code}')
                        error_model = None
                    raise SerpProAPIError(response.status_code, error_message, error_model)

            except (requests.exceptions.Timeout,
                    requests.exceptions.ReadTimeout,
                    requests.exceptions.ConnectTimeout):
                # При таймауте продолжаем цикл и делаем новую попытку
                print(f"Timeout occurred after {timeout} seconds. Retrying...")
                continue

            except requests.exceptions.RequestException as e:
                # Для всех остальных сетевых ошибок (не таймаут) - выбрасываем исключение
                raise SerpProAPIError(0, str(e))

    # ===== WORDSTAT METHODS =====

    def wordstat_frequency(self,
                          query: Optional[str] = None,
                          region: Optional[str] = None,
                          device: WordstatDevice = WordstatDevice.ALL,
                          task_type: WordstatTaskType = WordstatTaskType.REGULAR,
                          syntax: WordstatSyntax = WordstatSyntax.WS) -> FrequencyResponse:
        """
        Получает частотность запроса

        Args:
            query: Поисковый запрос
            region: Список регионов, разделенных запятой. Пример: "225" или "225,213"
            device: Тип устройства (не поддерживается для task_type=Direct)
            task_type: Тип задачи (Regular - обычный вордстат, Direct - Яндекс.Директ)
            syntax: Синтаксис запроса

        Returns:
            FrequencyResponse: Данные о частотности
        """
        request_data = FrequencyRequest(
            query=query,
            region=region,
            device=device,
            task_type=task_type,
            syntax=syntax
        )

        response_data = self._make_request('POST', '/api/v1/wordstat/frequency',
                                          request_data.model_dump(exclude_none=True))

        return FrequencyResponse(**response_data)

    def wordstat_deep(self,
                     query: Optional[str] = None,
                     region: Optional[str] = None,
                     device: WordstatDevice = WordstatDevice.ALL,
                     task_type: WordstatTaskType = WordstatTaskType.REGULAR) -> DeepResponse:
        """
        Получает постраничные данные по запросу (похожие и популярные запросы)

        Args:
            query: Поисковый запрос
            region: Список регионов, разделенных запятой
            device: Тип устройства (не поддерживается для task_type=Direct)
            task_type: Тип задачи (Regular - обычный вордстат, Direct - Яндекс.Директ)

        Returns:
            DeepResponse: Постраничные данные
        """
        request_data = DeepRequest(
            query=query,
            region=region,
            device=device,
            task_type=task_type
        )

        response_data = self._make_request('POST', '/api/v1/wordstat/deep',
                                          request_data.model_dump(exclude_none=True))

        return DeepResponse(**response_data)

    def wordstat_history(self,
                        query: str,
                        region: Optional[str] = None,
                        device: WordstatDevice = WordstatDevice.ALL,
                        grouping: WordstatGrouping = WordstatGrouping.MONTH,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None) -> HistoryResponse:
        """
        Получает исторические данные по запросу

        Args:
            query: Поисковый запрос (обязательный, 1-3000 символов)
            region: Список регионов, разделенных запятой
            device: Тип устройства
            grouping: Группировка данных по времени (Day, Week, Month)
            start_date: Начальная дата в формате "YYYY-MM-DD" (опционально)
            end_date: Конечная дата в формате "YYYY-MM-DD" (опционально)

        Returns:
            HistoryResponse: Исторические данные
        """
        request_data = HistoryRequest(
            query=query,
            region=region,
            device=device,
            grouping=grouping,
            start_date=start_date,
            end_date=end_date
        )

        response_data = self._make_request('POST', '/api/v1/wordstat/history',
                                          request_data.model_dump(exclude_none=True))

        return HistoryResponse(**response_data)

    # ===== REGION METHODS =====

    def region_yandex(self, query: str) -> List[RegionResponse]:
        """
        Получает список кодов регионов Yandex

        Args:
            query: Поисковый запрос (1-500 символов)

        Returns:
            List[RegionResponse]: Список регионов Yandex
        """
        params = {'query': query}
        response_data = self._make_request('GET', '/api/v1/region/yandex', params=params)
        return [RegionResponse(**item) for item in response_data]

    def region_google(self, query: str) -> List[RegionResponse]:
        """
        Получает список кодов регионов Google

        Args:
            query: Поисковый запрос (1-500 символов)

        Returns:
            List[RegionResponse]: Список регионов Google
        """
        params = {'query': query}
        response_data = self._make_request('GET', '/api/v1/region/google', params=params)
        return [RegionResponse(**item) for item in response_data]

    def region_check(self,
                    code: str,
                    search_system: SearchSystem,
                    search_type: RegionSearchType) -> List[RegionResponse]:
        """
        Проверяет наличие кода региона в базе кодов регионов Google или Yandex

        Args:
            code: Код региона (1-500 символов)
            search_system: Поисковая система (Yandex или Google)
            search_type: Тип поиска (Name или Code)

        Returns:
            List[RegionResponse]: Список найденных регионов
        """
        params = {
            'code': code,
            'searchSystem': search_system.value,
            'searchType': search_type.value
        }
        response_data = self._make_request('GET', '/api/v1/region/check', params=params)
        return [RegionResponse(**item) for item in response_data]

    # ===== FINANCE METHODS =====

    def finance_total(self, service: Optional[ServiceType] = None) -> FinanceStatsResponse:
        """
        Получает сумму всех запросов

        Args:
            service: Тип сервиса (опционально)

        Returns:
            FinanceStatsResponse: Общее количество запросов
        """
        params = {}
        if service:
            params['service'] = service.value

        response_data = self._make_request('GET', '/api/v1/finance/total', params=params)
        return FinanceStatsResponse(**response_data)

    def finance_statistics(self,
                          service_type: Optional[ServiceType] = None,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> FinanceStatsResponse:
        """
        Получает статистику за период

        Args:
            service_type: Тип сервиса (опционально)
            start_date: Начальная дата в формате "YYYY-MM-DD"
            end_date: Конечная дата в формате "YYYY-MM-DD"

        Returns:
            FinanceStatsResponse: Статистика запросов
        """
        request_data = FinanceStatsRequest(
            service_type=service_type,
            start_date=start_date,
            end_date=end_date
        )

        response_data = self._make_request('POST', '/api/v1/finance/statistics',
                                          request_data.model_dump(exclude_none=True))

        return FinanceStatsResponse(**response_data)


# ===== EXAMPLE USAGE =====

if __name__ == "__main__":
    # Инициализация клиента
    client = SerpProClient(
        api_key="your-api-key",
        verify_ssl=True
    )

    try:
        # ===== WORDSTAT EXAMPLES =====
        print("=== WORDSTAT ===")

        # Получение частотности (Regular - обычный Wordstat)
        frequency_result = client.wordstat_frequency(
            query="Король и Шут",
            region="225",
            device=WordstatDevice.ALL,
            task_type=WordstatTaskType.REGULAR,
            syntax=WordstatSyntax.WS
        )
        print(f"Frequency: {frequency_result.frequency}")

        # Получение частотности через Яндекс.Директ
        frequency_direct = client.wordstat_frequency(
            query="КиШ",
            region="225",
            task_type=WordstatTaskType.DIRECT,
            syntax=WordstatSyntax.WS
        )
        print(f"Frequency (Direct): {frequency_direct.frequency}")

        # Получение постраничных данных (Regular)
        deep_result = client.wordstat_deep(
            query="Король и Шут",
            region="225",
            device=WordstatDevice.ALL,
            task_type=WordstatTaskType.REGULAR
        )
        print(f"Deep associations: {len(deep_result.associations or [])}")
        print(f"Deep popular: {len(deep_result.popular or [])}")

        # Получение истории
        history_result = client.wordstat_history(
            query="Король и Шут",
            region="225",
            device=WordstatDevice.ALL,
            grouping=WordstatGrouping.MONTH,
            start_date="2025-07-01",
            end_date="2025-09-30"
        )
        print(f"History items: {len(history_result.items or [])}")

        # ===== REGION EXAMPLES =====
        print("\n=== REGION ===")

        # Поиск регионов Yandex
        yandex_regions = client.region_yandex(query="Москва")
        print(f"Yandex regions found: {len(yandex_regions)}")
        if yandex_regions:
            print(f"First region: {yandex_regions[0].name} ({yandex_regions[0].code})")

        # Поиск регионов Google
        google_regions = client.region_google(query="Moscow")
        print(f"Google regions found: {len(google_regions)}")

        # Проверка кода региона
        region_check = client.region_check(
            code="225",
            search_system=SearchSystem.YANDEX,
            search_type=RegionSearchType.CODE
        )
        print(f"Region check results: {len(region_check)}")

        # ===== FINANCE EXAMPLES =====
        print("\n=== FINANCE ===")

        # Получение общей статистики
        total = client.finance_total(service=ServiceType.WORDSTAT_FREQUENCY)
        print(f"Total requests: {total.request_count}")

        # Получение статистики за период
        stats = client.finance_statistics(
            service_type=ServiceType.WORDSTAT_FREQUENCY,
            start_date="2025-07-01",
            end_date="2025-10-06"
        )
        print(f"Period statistics: {stats.request_count}")

    except SerpProAPIError as e:
        print(f"API Error: {e}")
        if e.error_model:
            print(f"Error ID: {e.error_model.id}")
            print(f"Invalid data: {e.error_model.invalid_data}")
    except Exception as e:
        print(f"Unexpected error: {e}")
