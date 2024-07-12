from celery import Celery

# Inicjalizacja aplikacji Celery z backendem Redis
app = Celery(
    "tasks", broker="redis://localhost:6379/0", backend="redis://localhost:6379/0"
)

app.conf.update(
    result_backend="redis://localhost:6379/0",
    broker_url="redis://localhost:6379/0",
)
# Pobranie inspektora
inspector = app.control.inspect()

# Pobranie wszystkich zadań
tasks = inspector.active()

# Wyświetlenie wszystkich zadań
print(tasks)
