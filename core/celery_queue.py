from celery_tasks import scrap, add, fill
import time

from otodom_scraper import Scraper
from otodom_filler import Filler
from models import Session, CeleryTasks


def add_scrapes_to_queue(threads):
    object = Scraper()
    object.check_pages()
    links = object.pages_from_db()
    links = [links[4]]
    session = Session()
    for link in links:
        n_pages = link.num_pages
        chunk_size = 50
        for i in range(0, n_pages, chunk_size):
            start = i + 1
            size = min(chunk_size, n_pages - i)
            result = scrap.delay(link.type, start, size, threads)
        print(f"{link.type} added to queue")
    session.close()


def add_fillers_to_queue(threads):
    object = Filler()
    chunk_size = 1000
    all_id_list = object.take_data_from_db()
    n_offers = len(all_id_list)
    print(n_offers)
    session = Session()
    for i in range(0, n_offers, chunk_size):
        chunk = all_id_list[i : i + chunk_size]
        result = fill.delay(chunk,threads)
        task = CeleryTasks(task_id=result.id, type="address_filler")
        session.add(task)
        session.commit()
    session.close()


# if __name__ == "__main__":
#     add_fillers_to_queue(threads=5)


if __name__ == "__main__":
    add_scrapes_to_queue(threads=5)
