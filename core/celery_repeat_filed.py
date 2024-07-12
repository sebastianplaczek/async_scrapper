from celery import Celery
from celery.result import GroupResult

# Konfiguracja Celery
app = Celery("tasks", broker="pyamqp://", backend="rpc://")


def retry_failed_tasks():
    i = app.control.inspect()
    active_tasks = i.active()

    failed_tasks = []
    for worker, tasks in active_tasks.items():
        for task in tasks:
            result = AsyncResult(task["id"])
            if result.state == "FAILURE":
                failed_tasks.append(task["id"])

    if not failed_tasks:
        print("No failed tasks found.")
        return

    for task_id in failed_tasks:
        result = AsyncResult(task_id)
        task_name = result.name
        args = result.args
        kwargs = result.kwargs

        # Pobierz funkcję zadania po nazwie
        task = app.tasks[task_name]

        # Ponowne wysyłanie zadania
        task.apply_async(args=args, kwargs=kwargs)
        print(f"Retried task {task_name} with ID {task_id}")


def check_task_statuses():
    # Tworzymy instancję inspektora
    i = app.control.inspect()

    # Pobieramy informacje o zadaniach w różnych stanach
    active_tasks = i.active()
    reserved_tasks = i.reserved()
    scheduled_tasks = i.scheduled()

    print("Active tasks:")
    print(active_tasks)

    print("Reserved tasks:")
    print(reserved_tasks)

    print("Scheduled tasks:")
    print(scheduled_tasks)

    # Sprawdzanie statusu tasków na backendzie wyników
    for worker, tasks in active_tasks.items():
        for task in tasks:
            task_id = task["id"]
            result = app.AsyncResult(task_id)
            print(f"Task {task_id} status: {result.status}")


if __name__ == "__main__":
    check_task_statuses()
