import asyncio
import re

from yaqd_core import aserial, logging
logger = logging.getLogger("serial")


class SerialDispatcher:
    def __init__(self, port):
        self.port = port
        self.workers = {}
        self.write_queue = asyncio.Queue()
        self.loop = asyncio.get_event_loop()
        self.tasks = [
            self.loop.create_task(self.do_writes()),
            self.loop.create_task(self.read_dispatch()),
        ]

    def write(self, data):
        self.write_queue.put_nowait(data)

    async def do_writes(self):
        while True:
            data = await self.write_queue.get()
            logger.debug(f"write pop {data}")
            self.port.write(data)
            self.write_queue.task_done()
            await asyncio.sleep(0.001)

    async def read_dispatch(self):
        while True:
            try:
                reply = self.port.read()
            except:
                await asyncio.sleep(0.001)
            else:
                logger.debug(reply)
                if reply.device_number in self.workers:
                    self.workers[reply.device_number].put_nowait(reply)
                await asyncio.sleep(0)

    def flush(self):
        self.port.flush()

    def close(self):
        self.loop.create_task(self._close())

    async def _close(self):
        #await self.write_queue.join()
        for worker in self.workers.values():
            continue
            await worker.join()
        for task in self.tasks:
            task.cancel()