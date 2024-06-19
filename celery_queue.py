from celery_tasks import scrap, add, fill
import time

from otodom_scrapper import Otodom
from otodom_filler import Filler


def add_scrapes_to_queue():
    object = Otodom()
    object.check_pages()
    links = object.pages_from_db()
    for link in links:
        n_pages = link.num_pages
        chunk_size = 50
        for i in range(0, n_pages, chunk_size):
            start = i + 1
            size = min(chunk_size, n_pages - i)
            scrap.delay(link.type, start, size)


def add_fillers_to_queue():
    object = Filler()
    chunk_size = 1000
    all_id_list = object.take_data_from_db()
    n_offers = len(all_id_list)
    print(n_offers)
    for i in range(0, n_offers, chunk_size):
        chunk = all_id_list[i:i + chunk_size]
        fill.delay(chunk)
        # print(f"{i}:{i} + {chunk_size}")


if __name__ == "__main__":
    add_fillers_to_queue()
