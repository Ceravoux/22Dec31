"""worker."""

import asyncio
from tm import Time, Timezone
from database import DATABASE


class Worker:
    def __init__(self, *, loop: asyncio.AbstractEventLoop, bot):
        self.loop = loop

        self.current_task = []
        self.next_task = []
        self.to_do = []

        self.time: Time
        self.sleeping: asyncio.Future
        self.waker: asyncio.TimerHandle

        self.is_suspended = True
        self.is_running = False

        self.bot = bot

    def check(self, other):
        print(self.current_task, "------------COMPARE-------------", other)
        
        if not self.is_running:
            self.run()
            return

        if not self.current_task:
            print(1)
            self.current_task.append(other)

        elif other["posix_time"] < self.current_task[0]["posix_time"]:
            print(2)
            self.sleeping.cancel()

        elif other["posix_time"] == self.current_task[0]["posix_time"]:
            print(3)
            if self.sleeping.done():
                self._decide_to_do(other)
            else:
                self.current_task.append(other)

        elif (not self.next_task) or other["posix_time"] < self.next_task[0]["posix_time"]:
            print(4)
            self.next_task = [other]

        elif other["posix_time"] == self.next_task[0]["posix_time"]:
            print(5)
            self.next_task.append(other)


    async def _get_tasks(self):
        print("get task")
        self.current_task = [] or self.next_task
        self.next_task = []

        async for i in DATABASE.find({"completed": False}).sort("posix_time", 1):
            self.check(i)

        # maybe there is no data in db
        if not self.current_task:
            self.is_running = False
            return

        self.time = Time.from_seconds(
            self.current_task[0]["posix_time"],
            tzinfo=Timezone.from_string_offset(self.current_task[0]["timezone"]),
        )
        print("end get_task")
        print("current", self.current_task)
        print("next", self.next_task)

    def run(self) -> asyncio.Task:
        if self.is_running:
            print("Worker is already running!")
            return
        self.is_running = True
        self.is_suspended = False
        return self.loop.create_task(self._run())

    async def _run(self):

        await self._get_tasks()

        while self.is_running:
            try:
                self.sleeping = self.loop.create_future()
                self.waker = self.loop.call_later(
                    self.time.to_seconds_from_now(), self.sleeping.set_result, 1
                )
                await self.sleeping

            except Exception as e:
                # in case there's an error with
                # time.to_seconds_from_now()
                print("in _run():", e)
                continue

            except asyncio.CancelledError:
                pass
            else:
                print("current tasks:", self.current_task)
                print("next tasks:", self.next_task)
                try:
                    for i in self.current_task:
                        await self._decide_to_do(i)

                    await asyncio.gather(call(), *self.to_do)
                except Exception as e:
                    raise e
                self.to_do = []
            finally:
                await self._get_tasks()

    async def _decide_to_do(self, task):
        user = await self.bot.get_or_fetch_user(task["user"])
        # in case user is banned
        if not user:
            self.to_do.append(DATABASE.delete_many({"user": user.id}))
            return
        if task["once"]:
            self.to_do.append(DATABASE.delete_one(task))
        else:
            t = self.time.to_next_week()
            self.to_do.append(
                DATABASE.update_one(
                    task, {"$set": {"time": t, "posix_time": t.to_seconds()}}
                )
            )
        self.to_do.append(
            user.send(
                f'{Time.now(tz=Timezone.from_string_offset(task["timezone"]))}: {task["details"]}'
            )
        )

    def cancel(self, task):
        if task["posix_time"] == self.time.to_seconds():
            self.current_task.remove(task)
            if not self.current_task:
                self.sleeping.cancel()
        else:
            self.to_do.append(DATABASE.delete_one(task))

    def edit(self, task, new):
        if task["posix_time"] == self.time.to_seconds():
            self.current_task.remove(task)
            self.current_task.append(new)
        else:
            self.to_do.append(DATABASE.update_one(task, new))

    def suspend(self):
        if not self.is_running or self.is_suspended:
            return
        if not self.sleeping.done():
            self.waker.cancel()
            self.is_suspended = True
        self.is_running = False

    def continue_loop(self):
        if self.is_running:
            return
        if not self.sleeping.done():
            self.sleeping.set_result(1)
        self.run()


async def call():
    print("call at", Time.now())
