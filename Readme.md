# Примеры для использования API moab-apis.ru

Язык программирования: python

Перед началом работы необходимо выполнить команду:

```
pip install -r requirements.txt
```

Пример использования:

```
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
```
