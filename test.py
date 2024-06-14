import time
import random

import asyncio
import aiohttp


class AsyncTester:

    def __init__(self):
        self.sleeps = [random.randint(5, 10) for _ in range(0, 1000)]
        self.semaphore = asyncio.Semaphore(50)
        self.lock = asyncio.Lock()
        self.active_count = 0
        self.counter = 0

    async def worker(self, sleep_time):
        self.counter += 1
        asyncio.sleep(sleep_time)

    async def run_task(self, sleep_time):
        async with self.semaphore:
            async with self.lock:
                self.active_count += 1
                print(
                    f"Started processing:{self.counter}, Active processes: {self.active_count}"
                )
            await self.worker(sleep_time)
            async with self.lock:
                self.active_count -= 1
                print(
                    f"Finished processing:{self.counter}, Active processes: {self.active_count}"
                )

    async def run_all_tasks(self):
        tasks = []
        for rand in self.sleeps:
            tasks.append(self.run_task(rand))
        await asyncio.gather(*tasks)

    def run(self):
        asyncio.run(self.run_all_tasks())


if __name__ == "__main__":
    model = AsyncTester()
    model.run()
