from celery_tasks import scrap, add
import time

from otodom_scrapper import Otodom

if __name__ == "__main__":
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
