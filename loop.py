from utils import create_random_Schema, random_time, random_seconds
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from tm import Time, Timezone

client = AsyncIOMotorClient(
    "mongodb+srv://Valls:valleriane77@cluster0.d5ix9.mongodb.net/kms?retryWrites=true&w=majority",
    serverSelectionTimeoutMS=5000,
)
try:
    DATABASE = client["project"]["project02"]
except Exception as e:
    print(f"{e}: Unable to connect to the server.")


class Loop:
    def __new__(cls, *, loop: asyncio.AbstractEventLoop, bot):
        self = super().__new__(cls)
        self.loop: asyncio.AbstractEventLoop = loop or asyncio.new_event_loop()
        self.current_task = []
        self.next_task = []
        self.time = None
        self.users = []
        self.sleeping = None
        self.is_running = False
        self.bot = bot
        return self

    async def check(self, other):
        if self.current_task[0]["posix_time"] < other["posix_time"]:
            if not self.sleeping.done():
                self.cancel()

    async def _get_tasks(self):
        self.current_task = [] or self.next_task
        self.next_task = []

        async for i in DATABASE.find().sort("posix_time", 1):
            if not self.current_task:
                self.current_task.append(i)
            elif (
                self.next_task == []
                and self.current_task[0]["posix_time"] != i["posix_time"]
            ):
                print("   current_task:", self.current_task[0]["posix_time"])
                print("   i =", i["posix_time"])
                self.next_task.append(i)
            elif i["posix_time"] == self.current_task[0]["posix_time"]:
                self.current_task.append(i)
            elif i["posix_time"] == self.next_task[0]["posix_time"]:
                self.next_task.append(i)

        # maybe there is no data in db
        if not self.current_task:
            self.is_running = False
            return
        self.is_running = True

        self.time = Time.from_seconds(
            self.current_task[0]["posix_time"],
            tzinfo=Timezone.from_offset(self.current_task[0]["timezone"]),
        )
        print("current", self.current_task)
        print("next", self.next_task)

    def run(self):
        return self.loop.create_task(self._run())

    async def _run(self):
        if self.is_running:
            return

        await self._get_tasks()

        while self.is_running:
            try:
                self.sleeping = self.loop.create_future()
                self.handle = self.loop.call_later(
                    self.time.to_seconds_from_now(), self.sleeping.set_result, 1
                )
                await self.sleeping

            except ValueError as e:
                # in case there's an error with
                # time.to_seconds_from_now()
                print("in _run(): ValueError:", e.with_traceback(), e.args)

            except asyncio.CancelledError:
                continue

            else:
                to_do = []
                for i in self.current_task:
                    user = await self.bot.get_or_fetch_user(i["user"])
                    if not user:
                        to_do.append(DATABASE.delete_many({"user": user.id}))
                        continue
                    if i["once"]:
                        to_do.append(DATABASE.delete_one(self.current_task))
                        continue
                    t = self.time.to_next_week()
                    to_do.append(
                        DATABASE.update_one(
                            i, {"$set": {"time": t, "posix_time": t.to_seconds()}}
                        )
                    )
                    to_do.append(
                        user.send(
                            f'{self.current_task[0]["time"]}: '
                            f'{self.current_task["details"]}'
                        )
                    )

                await asyncio.gather(call(), *to_do)
                await self._get_tasks()


# import datetime


# async def foo():
#     await DATABASE.drop()
#     p = await DATABASE.create_index("time", expireAfterSeconds=0)
#     for i in range(5):
#         for n in range(20):
#             t = Time.from_seconds(
#                 Time.now().to_seconds() + 60 + i * 60 + n, tzinfo=datetime.timezone.utc
#             )
#             await DATABASE.insert_one(
#                 {
#                     "user": f"{i}-{n}",
#                     "details": str(t),
#                     "timezone": t.tzinfo,
#                     "time": t,
#                     "posix_time": t.to_seconds(),
#                     "once": t.once,
#                 }
#             )
#     print(await DATABASE.count_documents({}))


async def call():
    print("call at", Time.now())


# async def push_to_db(t=Time.from_seconds(Time.now().to_seconds() + 70)):
#     await DATABASE.insert_one(
#         {
#             "user": "6969",
#             "details": str(t),
#             "timezone": t.tzinfo,
#             "time": t,
#             "posix_time": t.to_seconds(),
#             "once": t.once,
#         }
#     )
#     print("inserted", t, "at", Time.now())

#     await asyncio.sleep(5)
#     return await push_to_db(t.from_seconds(t.to_seconds() + 10))


# loop = asyncio.new_event_loop()
# l = Loop(loop=loop)


# async def x():
#     await asyncio.gather(l.run(), push_to_db())


# loop.run_until_complete(foo())
# loop.run_until_complete(x())
