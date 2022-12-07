from utils import create_random_Schema, random_time, random_seconds
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from tm import Time, Timezone

client = AsyncIOMotorClient("mongodb+srv://Valls:valleriane77@cluster0.d5ix9.mongodb.net/kms?retryWrites=true&w=majority", serverSelectionTimeoutMS=5000)
try:
    DATABASE = client["project"]["project02"]
except Exception as e:
    print(f"{e}: Unable to connect to the server.")

class Loop:

    def __new__(cls, *, loop):
        self = super().__new__(cls)
        self.loop:asyncio.AbstractEventLoop = loop or asyncio.new_event_loop()
        self.current_task = []
        self.next_task = []
        self.sleeping = None
        return self

    async def check(self, other):
        if self.current_task[0]["posix_time"] < other["posix_time"]:
            if not self.sleeping.done():
                self.cancel()

        
    async def get_tasks(self):
        self.current_task = [] or self.next_task
        self.next_task = []

        async for i in DATABASE.find().sort("posix_time", 1):
            if not self.current_task:
                self.current_task.append(i)
            elif self.next_task == [] and self.current_task != i:
                self.next_task.append(i)
            elif i["posix_time"] == self.current_task[0]["posix_time"]:
                self.current_task.append(i)
            elif i["posix_time"] == self.next_task[0]["posix_time"]:
                self.next_task.append(i)

        self.time = Time.from_seconds(
            self.current_task[0]["posix_time"], 
            tzinfo=Timezone.from_offset(self.current_task[0]["timezone"])
        )
        print("current", self.current_task)
        print("next", self.next_task)

        # self.user = await self.get_or_fetch_user(self.current_task["userid"])
        # if not self.user:
            # DATABASE.delete_many({"userid": self.current_task["userid"]})
            # return await self.get_tasks()

    async def run(self):
        await self.get_tasks()
        while True:
            try:
                self.sleeping = self.loop.create_future()
                self.handle = self.loop.call_later(
                    self.time.to_seconds_from_now(), 
                    self.sleeping.set_result, 
                    1
                )
                await self.sleeping

            except ValueError as e:
                # in case there's an error with 
                # time.to_seconds_from_now()
                print(e.with_traceback(), e.args)
            
            except asyncio.CancelledError:
                continue
                
            else:
                to_do = []
                for i in self.current_task:
                    if i["once"]:
                        to_do.append(DATABASE.delete_one(self.current_task)) 
                        continue
                    self.time = self.time.to_next_week()
                    print("time", self.time)
                    to_do.append(
                        DATABASE.update_one(i, {
                            "$set": {
                                "time":self.time, 
                                "posix_time":self.time.to_seconds()
                            }
                        }))
                
                await asyncio.gather(
                    call(),
                    # self.user.send(f'{self.current_task["time"]}: '
                    #             f'{self.current_task["details"]}'),
                    *to_do
                    )
                await self.get_tasks()
   

async def foo():
    await DATABASE.drop()
    # from test import Sche
    p = await DATABASE.create_index("time", expireAfterSeconds=0)
    for i in range(5):
        for n in range(20):
            t = Time(2022, 12, 7, 17, 54 + i, n)
            await DATABASE.insert_one({"userid":f"{i}-{n}", "details": str(t), "timezone": t.tzinfo, "time": t, "posix_time": t.to_seconds(), "once":t.once})
    print(await DATABASE.count_documents({}))
    # print(await DATABASE.find_one({}))
    # for i in range(10):
    #     await asyncio.sleep(60)
    #     print(await DATABASE.count_documents({}))

async def call():
    print("call at", Time.now())

loop = asyncio.new_event_loop()
l = Loop(loop=loop)
loop.run_until_complete(foo())
loop.run_until_complete(l.run())

# asyncio.run(foo())
