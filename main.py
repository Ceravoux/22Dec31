import disnake
from disnake.ext.commands import String
import asyncio
from schema import Schema
from tm import Time, Timezone, Weekdays, TimezoneChoices
from database import database
from instances import bot, worker
from utils import taskListView, Select, format_task
from os import getenv
from dotenv import load_dotenv

load_dotenv()


@bot.listen()
async def on_disconnect():
    if worker.is_running:
        worker.suspend()
        print(worker.is_suspended)
    # XXX freeze database
    print("disconnected")


@bot.listen()
async def on_ready():
    print("Resuming worker...")
    if worker.is_suspended:
        worker.continue_loop()
        print(worker.is_running)

    # Some datas could be called while the bot
    # was dead, so update the data to keep up
    # with the present.
    # now = Time.now()
    # later = Time.from_seconds(now.to_seconds() + 60)

    # async for i in database.find({"time": {"$lt": now}}):
    #     print(i)
    #     to_later = i.copy()
    #     to_later.update({"posix_time": later.to_seconds(), "once": True})
    #     await database.insert_one(to_later)
    #     print(to_later)
    #     if not i["once"]:
    #         t = Time.from_seconds(i["posix_time"]).to_next_week()
    #         result = await database.update_one(
    #             i, {"$set": {"time": t, "posix_time": t.to_seconds()}}
    #         )
    #         print(result)
    #         continue
    print("end ready")


@bot.slash_command()
async def create_schedule(
    inter: disnake.AppCmdInter,
    timezone: TimezoneChoices,
    weekday: Weekdays,
    time: String[3, 8],
    details: String[1, 48],
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
    try:
        data = Schema(
            user=inter.author.id,
            details=details,
            timezone=timezone,
            weekday=weekday,
            time=time,
            once=False,
        )
    except ValueError as e:
        return await inter.response.send_message(e.args[0])

    exists = await database.find_one({"user": data.user, "posix_time": time})
    if exists:
        return await inter.response.send_message(
            f"You have already created a schedule at {data.time}, "
            "you can edit the schedule or cancel it and create a new one"
        )
    data = data.to_db()
    await asyncio.gather(
        database.insert_one(data),
        inter.response.send_message("Successfully scheduled!", ephemeral=True),
    )

    worker.check(data)


@bot.slash_command()
async def create_task(
    inter: disnake.AppCmdInter,
    timezone: TimezoneChoices,
    date: String[3, 10],
    time: String[3, 8],
    details: String[1, 48],
):
    """
    Creates a one-time task.

    Parameters
    ----------
    timezone: in UTC; e.g. -09:45 or +12:00 (defaults to UTC+00)
    date: YYYY/MM/DD e.g. 2022/12/26 or "today" for today
    time:HH:MM:SS e.g. 4:30 or 21:42:55
    details: e.g. Buy some groceries
    """
    try:
        data = Schema(
            user=inter.author.id,
            details=details,
            timezone=timezone,
            date=date,
            time=time,
            once=True,
        )
    except ValueError as e:
        return await inter.response.send_message(e.args[0])

    exists = await database.find_one({"user": data.user, "posix_time": time})
    if exists:
        return await inter.response.send_message(
            f"You have already created a task at {data.time}, "
            "you can edit the task or cancel it and create a new one"
        )
    data = data.to_db()
    await asyncio.gather(
        database.insert_one(data),
        inter.response.send_message("Successfully scheduled!", ephemeral=True),
    )

    worker.check(data)


@bot.slash_command()
async def task_list(inter: disnake.AppCmdInter):
    """
    Displays your list of schedules and tasks.
    """

    emb = disnake.Embed(
        title=f"{inter.author.name}'s tasks", colour=3046752
    ).set_author(name=inter.author.display_name, icon_url=inter.author.display_avatar)

    schedule = {}
    tasks = []

    async for i in database.find({"user": inter.author.id}).sort("posix_time", 1):
        tz = Timezone.from_string_offset(i["timezone"])
        i["time"] = Time.from_seconds(i["posix_time"], tzinfo=tz)
        if i["once"]:
            tasks.append(format_task(i))
            continue

        wd = i["time"].weekday
        if not wd in schedule.keys():
            schedule[wd] = []

        schedule[wd].append((i["_id"], f'{i["time"].time()} - {i["details"]}\n'))

    string = ""
    schedule = sorted(schedule.items(), key=lambda x: Weekdays[x[0]])

    for wd, daytask in schedule:
        string += wd + "\n"
        for task in daytask:
            string += task[1]
        string += "\n"

    emb.add_field(
        name="Schedule", 
        value=string or "You have no schedule set.", 
        inline=False
    )
    emb.add_field(
        name="Tasks",
        value="".join(t[1] for t in tasks) or "You have no tasks set.",
        inline=False,
    )

    await inter.response.send_message(
        embed=emb, ephemeral=True, view=taskListView(tasks, schedule)
    )


@bot.slash_command()
async def mark_as_done(inter: disnake.AppCmdInter):
    """Marks task(s) as done so that they won't be reminded."""
    tasks = [
        format_task(i)
        async for i in database.find(
            {"user": inter.author.id, "completed": False, "once": True}
        )
    ]
    await inter.response.send_message(
        view=disnake.ui.View(timeout=90).add_item(Select("markasdone", tasks)),
        ephemeral=True,
    )


@bot.slash_command()
async def help(inter: disnake.AppCmdInter):
    """Shows some information about the bot."""
    embed = HelpEmbed
    return await inter.response.send_message(embed=embed, ephemeral=True)


HelpEmbed = disnake.Embed(title="Help", colour=588228)
HelpEmbed.add_field(
    name="Purpose",
    value="Organise your time with schedules(weekly reminders) "
    "and tasks(one-time reminder).\n"
    "You can mark tasks as done if you do not wish the bot "
    "to remind you about it. However, they cannot be kept "
    "forever, and are removed once their time is due.",
)

HelpEmbed.add_field(
    name="How to use",
    value="Invoke `/create_schedule` to create a schedule, or "
    "`/create_task` to create a task. You have to "
    "include your timezone (in UTC), the time for "
    "this schedule/task is due, and the details of "
    "what they are about.\nFor schedules, you provide "
    "the weekday this schedule should be called, "
    "if it is earlier than today, it will be start "
    "to be called next week instead.\nFor tasks, "
    "you must provide a time that is sooner than "
    "now but less than 183 days from now.\n\n"
    "You can also list out your schedules and tasks "
    "by invoking `/tasks_list`, as well as editting "
    "the details or cancelling any calls",
)
HelpEmbed.add_field(
    name="Bugs and Issues",
    value="Should you encounter any bug or issue related to "
    "this service, please contact Vallery#0627",
)
HelpEmbed.add_field(name="ToS", value="...")


bot.run(getenv("TOKEN"))
