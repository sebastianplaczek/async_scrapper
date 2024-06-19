from celery import Celery
import time

from otodom_scrapper import Otodom
from otodom_filler import Filler

# broker = "amqp://guest:guest@localhost:5672/"
app = Celery("tasks", broker="pyamqp://", backend="rpc://")

app.conf.update(broker_connection_retry_on_startup=True)


@app.task
def scrap(type, start_page, chunk_size):
    model = Otodom(save_to_db=True)
    model.scrap_pages(type, start_page, chunk_size)


@app.task
def fill(id_list):
    model = Filler()
    model.update_chunk_rows(id_list)


@app.task
def add(x, y):
    return x + y
