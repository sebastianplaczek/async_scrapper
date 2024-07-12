from models import Session,CeleryTasks
from celery.result import AsyncResult
import time

session = Session()


def check_and_update_tasks():
    while True:
        tasks = session.query(CeleryTasks).filter(CeleryTasks.done == 0).all()
        if not tasks:
            print('All tasks finished')
            break  # Exit loop if no tasks need to be processed

        for task in tasks:
            result = AsyncResult(task.task_id)  # Use task.task_id instead of task_id

            print(f"Task ID: {task.task_id}, Status: {result.status}")
            if result.successful() or result.failed():
                task.status = result.status
                task.done = True
                task.time_start = result.time_start
                task.time_end = result.time_end
                task.runtime = (time_end - time_start).total_seconds()
                session.commit()
            else:
                continue
        time.sleep(120)


if __name__ == "__main__":
    check_and_update_tasks()
    session.close()
