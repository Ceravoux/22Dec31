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


class MyCogs(commands.Cog):
    def __init__(self, *, bot) -> None:
        super().__init__()
        self.bot = bot
        self.worker = Loop(loop=self.bot.loop, bot=self.bot)

    @commands.Cog.listener()
    async def on_ready(self):
        await DATABASE.drop()
        print(self.bot.loop)
        print(await self.bot.get_or_fetch_user(756056148058177596))
    
    @commands.Cog.listener()
    async def on_disconnect(self):
        if self.worker.is_running:
            self.worker.suspend()

    @commands.Cog.listener()
    async def on_resumed(self):
        if self.worker.is_suspended:
            self.worker.continue_loop()

    @commands.slash_command(guild_ids=[1048908479202594878])
    async def create_schedule(
        self,
        inter: disnake.AppCmdInter,
        timezone: TimezoneChoices,
        weekday: Weekdays,
        time: commands.String[8, 8],
        details: commands.String[1, 48],
    ):
        """
        Creates a weekly task.

        Parameters
        ----------
        timezone: only supports UTC; e.g. -09:00 for UTC-09:00 (defaults to UTC+00)
        weekday: Mon/Tue/Wed/Thu/Fri/Sat/Sun
        time: e.g. 08:42:15
        details: e.g. Feed dog homework
        """
        t = Time.from_weekday(
            weekday,
            *[int(i) for i in time.split(":")],
            tzinfo=Timezone.from_string_offset(timezone),
        )
        data = Schema(
            user=inter.author.id,
            details=details,
            timezone=timezone,
            time=t,
            once=t.once,
            posix_time=t.to_seconds(),
        )
        await asyncio.gather(
            DATABASE.insert_one(data.to_db()),
            inter.response.send_message("Successfully scheduled!", ephemeral=True),
        )
        if self.worker.is_running:
            self.worker.check(data.posix_time)
            print("hmm")

        else:
            self.worker.run()
            print("hm")

    @commands.slash_command(guild_ids=[1048908479202594878])
    async def create_task(
        self,
        inter: disnake.AppCmdInter,
        timezone: TimezoneChoices,
        weekday: Weekdays,
        time: commands.String[8, 8],
        details: commands.String[1, 48],
    ):
        """
        Creates a one-time task.

        Parameters
        ----------
        timezone: in UTC; e.g. -09:45 or +12:00 (defaults to UTC+00)
        weekday: Mon/Tue/Wed/Thu/Fri/Sat/Sun
        time: e.g. 08:42:15
        details: e.g. Feed dog homework
        """

        print(DATABASE)
        t = Time.from_weekday(
            weekday,
            *[int(i) for i in time.split(":")],
            tzinfo=Timezone.from_string_offset(timezone),
        )
        print(t)
        t.run_once()
        data = Schema(
            user=inter.author.id,
            details=details,
            timezone=timezone,
            time=t,
            once=t.once,
            posix_time=t.to_seconds(),
        )
        await asyncio.gather(
            DATABASE.insert_one(data.to_db()),
            inter.response.send_message("Successfully scheduled!", ephemeral=True),
        )
        if self.worker.is_running:
            self.worker.check(data.posix_time)
            print("hmmm")

        else:
            tas = self.worker.run()
            print(asyncio.all_tasks(loop=self.worker.loop))
            print("hmmm5")


    @commands.slash_command(guild_ids=[1048908479202594878])
    async def create_schedule_modal(self, inter: disnake.AppCmdInter):
        await inter.response.send_modal(modal=MyModal(inter))

    # @commands.slash_command(guild_ids=[1048908479202594878])
    # async def create_task_modal(self, inter: disnake.AppCmdInter):
    #     await inter.response.send_modal(modal=MyModal(inter))

    @commands.slash_command(guild_ids=[1048908479202594878])
    async def edit(self, inter: disnake.AppCmdInter, time, details):
        """
        Edits the details of a task/schedule.

        Parameters
        ----------
        time: the time of the task/schedule to be edited
        details: new description
        """
        if inter.author == self.user:
            self.worker.sleeping.cancel()

        result = await DATABASE.update_one(
            {"user": inter.author.id, "time": time},
            {"$set": {"details": details}},
        )

        if result.modified_count == 0:
            await inter.response.send_message("No result.", ephemeral=True)
        else:
            await inter.response.send_message(
                f"Successfully edited!", ephemeral=True
            )

    @commands.slash_command(guild_ids=[1048908479202594878])
    async def cancel(self, inter: disnake.AppCmdInter, time):
        """
        Cancels a task/schedule.

        Parameter
        ---------
        time: the time of the task/schedule to be cancelled
        """
        if inter.author == self.user:
            self.worker.sleeping.cancel()

        result = await DATABASE.delete_one({"user": inter.author.id, "time": time})

        if result.deleted_count == 0:
            await inter.response.send_message("No result.", ephemeral=True)
        else:
            await inter.response.send_message("Task deleted!", ephemeral=True)

    @commands.slash_command(guild_ids=[1048908479202594878])
    async def task_list(self, inter: disnake.AppCmdInter):
        """
        Displays your list of schedules and tasks.
        """

        emb = disnake.Embed(
            title=f"{inter.author.name}'s tasks", colour=3046752
        ).set_author(
            name=inter.author.display_name, icon_url=inter.author.display_avatar
        )

        schedule = {}
        tasks = ""
        async for i in DATABASE.find({"user": inter.author.id}).sort("posix_time", 1):
            tz = Timezone.from_string_offset(i["timezone"])
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

        emb.add_field(name="Schedule", value=string or "\u200b", inline=False)
        emb.add_field(name="Unfinished Tasks", value=tasks or "\u200b", inline=False)

        await inter.response.send_message(embed=emb, ephemeral=True)


bot = commands.InteractionBot()
bot.add_cog(MyCogs(bot=bot))
bot.run(getenv("TOKEN"))
