"""worker."""

import asyncio
from tm import Time, Timezone
from database import DATABASE


class Worker:
    def __init__(self, *, loop: asyncio.AbstractEventLoop, bot):
        self.loop = loop

        self._current_task = []
        self._to_do = []

        self._time: Time
        self._sleeping: asyncio.Future
        self._waker: asyncio.TimerHandle

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
        print(self._current_task, "------------COMPARE-------------", other)
        
        if not self._is_running:
            self.run()
            return

        if not self._current_task:
            print(1)
            self._current_task.append(other)

        elif other["posix_time"] < self._current_task[0]["posix_time"]:
            print(2)
            self._sleeping.cancel()

        elif other["posix_time"] == self._current_task[0]["posix_time"]:
            print(3)
            if self._sleeping.done():
                self._decide_to_do(other)
            else:
                self._current_task.append(other)
            
        # elif other["posix_time"] - self._current_task[0]["posix_time"] < 5:
        #     self.current_task.append(other)


    async def _get_tasks(self):
        print("get task")
        self._current_task = []

        async for i in DATABASE.find({"completed": False}).sort("posix_time", 1):
            self.check(i)

        # maybe there is no data in db
        if not self._current_task:
            self._is_running = False
            return

        self._time = Time.from_seconds(
            self._current_task[0]["posix_time"],
            tzinfo=Timezone.from_string_offset(self._current_task[0]["timezone"]),
        )
        print("end get_task")
        print("current", self._current_task)

    def run(self) -> asyncio.Task:
        if self._is_running:
            print("Worker is already running!")
            return
        self._is_running = True
        self._is_suspended = False
        return self.loop.create_task(self._run())

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
                # in case there's an error with
                # time.to_seconds_from_now()
                print("in _run():", e)
                pass

            except asyncio.CancelledError:
                pass

            else:
                print("current tasks:", self._current_task)
                try:
                    for i in self._current_task:
                        await self._decide_to_do(i)
                    await asyncio.gather(call(), *self._to_do)

                except Exception as e:
                    raise e

            finally:
                self._to_do = []
                await self._get_tasks()

    async def _decide_to_do(self, task):
        user = await self.bot.get_or_fetch_user(task["user"])
        # in case user is banned
        if not user:
            self._to_do.append(DATABASE.delete_many({"user": user.id}))
            return
        if task["once"]:
            self._to_do.append(DATABASE.delete_one(task))
        else:
            t = self._time.to_next_week()
            self._to_do.append(
                DATABASE.update_one(
                    task, {"$set": {"time": t, "posix_time": t.to_seconds()}}
                )
            )
        self._to_do.append(
            user.send(
                f'{Time.now(tz=Timezone.from_string_offset(task["timezone"]))}: {task["details"]}'
            )
        )

    def cancel(self, task):
        task = list(task)
        for i in task:
            if i["posix_time"] == self._time.to_seconds():
                self._current_task.remove(i)
                # if it becomes empty
                if not self._current_task:
                    return self._sleeping.cancel()

    def edit(self, task, new):
        if task["posix_time"] == self._time.to_seconds():
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
        if not self._sleeping.done():
            self._sleeping.set_result(1)
        self.run()


async def call():
    print("call at", Time.now())
