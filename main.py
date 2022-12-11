import disnake
from disnake.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from test import Schema
from tm import Time, Timezone
from loop import Loop
from os import getenv
from dotenv import load_dotenv
from utils import Weekdays, TimezoneChoices, MyModal
load_dotenv()


client = AsyncIOMotorClient(getenv("DB_KEY"), serverSelectionTimeoutMS=5000)
try:
    DATABASE = client["project"]["project01"]
except Exception as e:
    print(f"{e}: Unable to connect to the server.")


class MyClient(commands.InteractionBot):
    async def on_ready(self):
        
        self.handle = Loop(loop=self.loop, bot=self)
        print(self.loop)
        print(await self.get_or_fetch_user(756056148058177596))

    async def on_message(self, message: disnake.Message):
        if message.author == self.user:
            return
        # print(message.author)

        # await message.author.send("thonk")

    @commands.slash_command(guild_ids=[963069529968242789])
    async def create_schedule(
        self,
        inter: disnake.AppCmdInter,
        timezone: TimezoneChoices,
        weekday: Weekdays,
        time: commands.String[8, 8],
        details: commands.String[1, 48],
    ):
        """
        creates a weekly task.

        Parameters
        ----------
        timezone: only supports UTC; e.g. -09:00 for UTC-09:00 (defaults to UTC+00)
        weekday: Mon/Tue/Wed/Thu/Fri/Sat/Sun
        time: e.g. 08:42:15
        details: e.g. Feed dog homework
        """
        h, m, s = [int(i) for i in time.split(":")]
        t = Time.from_weekday(
            weekday,
            *[int(i) for i in time.split(":")],
            tzinfo=Timezone.from_string_offset(timezone),
        )
        data = Schema(
            user=inter.author.id,
            details=details,
            timezone=t.tzinfo,
            time=t,
            once=t.once,
            posix_time=t.to_seconds(),
        )
        await asyncio.gather(
            DATABASE.insert_one(str(data)),
            inter.response.send_message("Successfully scheduled!", ephemeral=True),
        )
        if self.handle.is_running:
            self.handle.check(data.posix_time)
        else:
            self.handle.run()

    @commands.slash_command(guild_ids=[963069529968242789])
    async def create_task(
        self,
        inter: disnake.AppCmdInter,
        timezone: TimezoneChoices,
        weekday: Weekdays,
        time: commands.String[8, 8],
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

        print(weekday)
        t = Time.from_weekday(
            weekday,
            *[int(i) for i in time.split(":")],
            tzinfo=Timezone.from_string_offset(timezone),
        )
        t.run_once()
        data = Schema(
            user=inter.author.id,
            details=details,
            timezone=t.tzinfo,
            time=t,
            once=t.once,
            posix_time=t.to_seconds(),
        )
        await asyncio.gather(
            DATABASE.insert_one(str(data)),
            inter.response.send_message("Successfully scheduled!", ephemeral=True),
        )
        if self.handle.is_running:
            self.handle.check(data.posix_time)
        else:
            self.handle.run()

    @commands.slash_command(guild_ids=[963069529968242789])
    async def create_schedule_modal(self, inter: disnake.AppCmdInter):
        await inter.response.send_modal(modal=MyModal(inter))

    # @commands.slash_command(guild_ids=[963069529968242789])
    # async def create_task_modal(self, inter: disnake.AppCmdInter):
    #     await inter.response.send_modal(modal=MyModal(inter))

    @commands.slash_command(guild_ids=[963069529968242789])
    async def edit(self, inter: disnake.AppCmdInter, time, details):
        if inter.author == self.user:
            self.handle.sleeping.cancel()

        result = await DATABASE.update_one(
            {"user": inter.author.id, "time": time},
            {"$set": {"time": time, "details": details}},
        )

        if result.modified_count == 0:
            await inter.response.send_message("No result.", ephemeral=True)
        else:
            await inter.response.send_message(
                f"Successfully edited to: {time} - {details}!", ephemeral=True
            )

    @commands.slash_command(guild_ids=[9630695299968242789])
    async def cancel(self, inter: disnake.AppCmdInter, time):
        if inter.author == self.user:
            self.handle.sleeping.cancel()

        result = await DATABASE.delete_one({"user": inter.author.id, "time": time})

        if result.deleted_count == 0:
            await inter.response.send_message("No result.", ephemeral=True)
        else:
            await inter.response.send_message("Task deleted!", ephemeral=True)

    @commands.slash_command(guild_ids=[963069529968242789])
    async def task_list(self, inter: disnake.AppCmdInter):

        emb = disnake.Embed(
            title=f"{inter.author.id}'s tasks", colour=3046752
        ).set_author(
            name=inter.author.display_name, icon_url=inter.author.display_avatar
        )

        schedule = {}
        tasks = ""
        async for i in DATABASE.find({"user": inter.author.id}).sort("posix_time", 1):
            tz = Timezone.from_string_offset(i["Timezone"])
            i["time"] = Time.from_seconds(i["posix_time"], tzinfo=tz)
            if i["once"]:
                tasks += f'{i["time"]} - {i["details"]}\n'
                continue

            wd = i["time"][:3]
            if not wd in schedule.keys():
                schedule[wd] = [{i["time"]: i["details"]}]
            else:
                schedule[wd].append({i["time"]: i["details"]})

        string = ""
        schedule = sorted(schedule.items(), key=lambda x: Weekdays[x[0]])
        for day, detail in schedule:
            string += day + "\n"
            for d in detail:
                string += d + "\n"
            string += "\n"

        emb.add_field(name="Schedule", value=string, inline=False)
        emb.add_field(name="Unfinished Tasks", value=tasks, inline=False)

        await inter.response.send_message(embed=emb, ephemeral=True)


bot = MyClient()
bot.run(getenv("TOKEN"))