# Примеры для использования API moab-apis.ru

Язык программирования: python

Перед началом работы необходимо выполнить команду:

```
pip install -r requirements.txt
```

Пример использования:

```
# Создание клиента
client = SerpProWordstatClient(api_key="your-api-key")

# Получение частотности запроса
frequency = client.get_frequency(
    query="Король и Шут", 
    region="225", 
    device=WordstatDevice.ALL
)

# Получение подробных данных
deep_data = client.get_deep(
    query="Король и Шут",
    region="225"
)

# Получение истории
history = client.get_history(
    query="Король и Шут",
    region="225", 
    grouping=WordstatGrouping.MONTH
)
```
