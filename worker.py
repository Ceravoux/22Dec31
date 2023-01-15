"""worker."""

import asyncio
from tm import Time, Timezone
from database import database
import traceback, sys

class Worker:
    def __init__(self, *, loop: asyncio.AbstractEventLoop, bot):
        self.loop = loop

        self._current_task = []
        self._to_do = []

        self._time: Time = None
        self._sleeping: asyncio.Future = self.loop.create_future()
        self._waker: asyncio.TimerHandle = None
        self.worker: asyncio.Task = None
        self._is_suspended = True
        self._is_running = False

        self.bot = bot

    @property
    def current_task(self):
        return self._current_task
    
    @property
    def time(self):
        return self._time

    @property
    def is_suspended(self):
        return self._is_suspended

    @property
    def is_running(self):
        return self._is_running

    def check(self, other):        
        if not self._is_running:
            self.run()
            return

        if not self._current_task:
            self._current_task.append(other)

        elif other["posix_time"] < self._current_task[0]["posix_time"]:
            self._sleeping.cancel()

        elif other["posix_time"] == self._current_task[0]["posix_time"]:
            if self._sleeping.done():
                self._decide_to_do(other)
            else:
                self._current_task.append(other)

    async def _get_tasks(self):
        self._current_task = []

        async for i in database.find({"completed": False}).sort("posix_time", 1):
            self.check(i)

        # maybe there is no data in db
        if not self._current_task:
            self._is_running = False
            return

        self._time = Time.from_seconds(
            self._current_task[0]["posix_time"],
            tzinfo=Timezone.from_string_offset(self._current_task[0]["timezone"]),
        )

    async def _run(self):

        await self._get_tasks()

        while self._is_running:
            try:
                self._sleeping = self.loop.create_future()
                self._waker = self.loop.call_later(
                    self._time.to_seconds_from_now(), self._sleeping.set_result, 1
                )
                await self._sleeping

            except Exception as e:
                print(f"Unhandled exception in internal background task {self.coro.__name__!r}.")
                traceback.print_exception(
                    type(e),
                    e,
                    e.__traceback__,
                    file=sys.stderr,
                )
                pass

            except asyncio.CancelledError:
                pass

            else:
                for i in self._current_task:
                    await self._decide_to_do(i)
                await asyncio.gather(call(), *self._to_do)

            finally:
                self._to_do = []
                await self._get_tasks()

    async def _decide_to_do(self, task):
        user = await self.bot.get_or_fetch_user(task["user"])
        # in case user is banned
        if not user:
            self._to_do.append(database.delete_many({"user": user.id}))
            return
        if task["once"]:
            self._to_do.append(database.delete_one(task))
        else:
            t = self._time.to_next_week()
            self._to_do.append(
                database.update_one(
                    task, {"$set": {"time": t, "posix_time": t.to_seconds()}}
                )
            )
        self._to_do.append(
            user.send(
                f'{Time.now(tz=Timezone.from_string_offset(task["timezone"]))}: {task["details"]}'
            )
        )

    def cancel(self, task):
        if self._time and task["posix_time"] == self._time.to_seconds():
            self._current_task.remove(task)

            # if it becomes empty cancel sleep 
            # so we dont wait for nothing
            if not self._current_task:
                self._sleeping.cancel()

    def edit(self, task, new):
        if self._time and task["posix_time"] == self._time.to_seconds():
            self._current_task.remove(task)
            self._current_task.append(new)

    def suspend(self):
        if not self._is_running or self._is_suspended:
            return
        if not self._sleeping.done():
            self._waker.cancel()
        self._is_suspended = True
        self._is_running = False

    def continue_loop(self):
        if self._is_running:
            return
        self.run()

    def run(self):
        if self._is_running:
            print("Worker is already running!")
            return
        self._is_running = True
        self._is_suspended = False
        if self.worker is not None:
            self.worker.cancel("continue_loop")
        self.worker = self.loop.create_task(self._run())

async def call():
    print("call at", Time.now())