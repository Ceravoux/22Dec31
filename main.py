import disnake
from disnake.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from test import Schema
from tm import Time, Timezone
from os import getenv
from dotenv import load_dotenv
load_dotenv()
from utils import Weekdays, MyModal


client = AsyncIOMotorClient(getenv("DB_KEY"), serverSelectionTimeoutMS=5000)
try:
    DATABASE = client["project"]["project01"]
except Exception as e:
    print(f"{e}: Unable to connect to the server.")


class MyClient(commands.Bot):
    
    async def on_ready(self):
        self.schedule = Loop()
        print(self.loop)
        print(await self.get_or_fetch_user(756056148058177596))
        
    
    async def on_message(self, message:disnake.Message):
        if message.author == self.user: return
        print(message.author)
        

        await message.author.send("thonk")

    @commands.slash_command(guild_ids=[963069529968242789])
    async def create_schedule(
        self, 
        inter: disnake.AppCmdInter, 
        timezoneUTC:commands.String[6,6],
        weekday: Weekdays,
        time: commands.String[8,8],
        details: commands.String[1, 48],
        ):
        """
        creates a weekly task.
        
        Parameters
        ----------
        timezone: only supports UTC; e.g. UTC-09 (defaults to UTC+00)
        weekday: Mon/Tue/Wed/Thu/Fri/Sat/Sun
        time: e.g. 08:42:15
        details: e.g. Feed dog homework
        """
        h, m, s = [int(i) for i in time.split(":")]
        t = Time.from_weekday(weekday, *[int(i) for i in time.split(":")], tzinfo=Timezone(int(timezoneUTC)))
        data = Schema(
            userid=inter.author.id, 
            details=details, 
            timezone=t.tzinfo, 
            time=t, 
            once=t.once, 
            posix_time=t.to_seconds()
        )
        await asyncio.gather(
            DATABASE.insert_one(str(data)), 
            inter.response.send_message("Successfully scheduled!", ephemeral=True)
        )

    @commands.slash_command(guild_ids=[963069529968242789])
    async def create_task(
        self, 
        inter: disnake.AppCmdInter, 
        timezoneUTC:commands.String[6,6],
        weekday: Weekdays,
        time: commands.String[8,8],
        details: commands.String[1, 48],
        ):
        """
        creates a one-time task.
        
        Parameters
        ----------
        timezone: in UTC; e.g. -09:45 or +12:00 (defaults to UTC+00)
        weekday: Mon/Tue/Wed/Thu/Fri/Sat/Sun
        time: e.g. 08:42:15
        details: e.g. Feed dog homework
        """
        
        t = Time.from_weekday(weekday, *[int(i) for i in time.split(":")], tzinfo=Timezone(int(timezoneUTC)))
        t.run_once()
        data = Schema(
            userid=inter.author.id, 
            details=details, 
            timezone=t.tzinfo, 
            time=t, 
            once=t.once, 
            posix_time=t.to_seconds()
        )
        await asyncio.gather(
            DATABASE.insert_one(str(data)), 
            inter.response.send_message("Successfully scheduled!", ephemeral=True)
        )
        if self.handle is None:
            ...

    @commands.slash_command(guild_ids=[963069529968242789])
    async def create_schedule_modal(self, inter: disnake.AppCmdInter):
        await inter.response.send_modal(modal=MyModal(inter))

    # @commands.slash_command(guild_ids=[963069529968242789])
    # async def create_task_modal(self, inter: disnake.AppCmdInter):
    #     await inter.response.send_modal(modal=MyModal(inter))

    @commands.slash_command(guild_ids=[963069529968242789])
    async def edit(self, inter: disnake.AppCmdInter, time, details):
        if inter.author == self.user:
            self.schedule.sleeping.cancel()

        result = await DATABASE.update_one(
            {"userid": inter.author.id, "time":time},
            {"$set":{"time":time, "details":details}})

        if result.modified_count == 0:
            await inter.response.send_message(
                "No result.", ephemeral=True)
        else:
            await inter.response.send_message(
                f"Successfully edited to: {time} - {details}!", 
                ephemeral=True
            )
        
    @commands.slash_command(guild_ids=[9630695299968242789])
    async def cancel(self, inter: disnake.AppCmdInter, time):
        if inter.author == self.user:
            self.schedule.sleeping.cancel()

        result = await DATABASE.delete_one(
            {"userid": inter.author.id, "time":time})

        if result.deleted_count == 0:
            await inter.response.send_message(
                "No result.", ephemeral=True)
        else:
            await inter.response.send_message(
                "Task deleted!", ephemeral=True)

    @commands.slash_command(guild_ids=[963069529968242789])
    async def task_list(self, inter: disnake.AppCmdInter):

        emb = disnake.Embed(
            title=f"{inter.author.id}'s tasks",
            colour=3046752
        ).set_author(
            name=inter.author.display_name, 
            icon_url=inter.author.display_avatar)

        schedule = {}
        tasks = ""
        async for i in DATABASE.find({"userid":inter.author.id}).sort("posix_time", 1):
            if i["once"]:
                tasks += f'{i["time"]} - {i["details"]}\n'
                continue

            # HACK: data is unsorted by weekday
            wd = i["time"][:3]
            if not wd in schedule.keys():
                schedule[wd] = [{i["time"]: i["details"]}]
            else:
                schedule[wd].append({i["time"]: i["details"]})

        # emb.add_field(name="Schedule", value=..., inline=False)
        emb.add_field(name="Unfinished Tasks", value=tasks, inline=False)

        await inter.response.send_message(
            embed=emb, ephemeral=True)


async def foo():
    res = await DATABASE.delete_one({"yourmom":0})
    print(res.deleted_count)
    print(res.raw_result)
    print(res.acknowledged)

    f = []
    async for i in DATABASE.find().sort("posix_time", 1):
        if len(f) < 2:
            f.append(i)
        elif i == f[1] or i == f[0]:
            f.append(i)
        else:
            break
    
    print(len(f))
    # f = await DATABASE.update_many(
    #     {
    #         "posix_time":{
    #             "$exists":True
    #         }
    #     }, 
    #     {
    #         "$set": {
    #             "posix_time":time.time() + random.randint(3600, 86400*2)
    #         }
    #     }
    # )
    # for i in range(10000):
    #     await DATABASE.insert_one(Schema.random_values().__dict__)

class Loop:

    def __new__(cls, bot:MyClient):
        self = super().__new__(cls)
        self.bot = bot
        self.current_task = None
    
    async def check(self, other):
        if self.current_task["posix_time"] < other:
            self.current_task =  other
            if not self.sleeping.done():
                self.cancel()

        elif self.next_task["posix_time"] < other:
            self.next_task = other
        
    async def get_tasks(self):
        self.next_task = self.current_task
        f = []
        async for i in DATABASE.find().sort("posix_time", 1):
            if len(f) < 2:
                f.append(i)
            elif i["posix_time"] == f[1]["posix_time"] \
              or i["posix_time"] == f[0]["posix_time"]:
                f.append(i)
            
        self.time = Time.from_seconds(
            self.current_task["posix_time"], 
            tzinfo=Timezone.from_offset(self.current_task["timezone"])
        )

        self.user = await self.bot.get_or_fetch_user(self.current_task["userid"])
        if not self.user:
            DATABASE.delete_many({"userid": self.current_task["userid"]})
            return await self.get_tasks()
        

    async def loop(self):
        await self.get_tasks()
        while True:
            try:
                self.sleeping = self.bot.loop.create_future()
                self.handle = self.bot.loop.call_later(
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
                if self.current_task["once"]:
                    to_do = DATABASE.delete_one(self.current_task)  
                else:
                    self.time = self.time.to_next_week()
                    to_do = DATABASE.update_one(
                        self.current_task,
                        {"$set": {"time":str(self.time), "posix_time":self.time.to_seconds()}}
                    )
                
                await asyncio.gather(
                    self.user.send(f'{self.current_task["time"]}: '
                                f'{self.current_task["details"]}'),
                    to_do
                    )
                await self.get_tasks()
                

import time
import random
start = time.time()
asyncio.run(foo())
print(f"end = {time.time()-start}")


# MyClient().run("OTU0MjYyNjQ3NjU2ODMzMDk0.YjQkWA.4uMZ60Bkr-0esVSqEyJElqsox-8")
