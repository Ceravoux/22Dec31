import aiofiles
from enum import Enum
import disnake
from test import Schema
import random, time, string

def random_time():
    return time.time() + random.randint(120, 3600)

def random_seconds(start, stop):
    return random.randrange(start, stop)

def create_random_Schema():
    return Schema(
        user=random.randint(100000000, 9999999999), 
        details=''.join([random.choice(list(string.ascii_letters)) for _ in range(random.randint(10, 48))]), 
        timezone="UTC"+random.choice("+-")+str(random.randint(0, 23)),
        time="urmom",
        once=True,
        posix_time=time.time() + random.randint(3600, 86400*2)
    )

async def to_table(data: dict, filename: str):
    if not isinstance(data, dict):
        raise ValueError(f"data has to be ``dict``, provided {type(data)}")

    async with aiofiles.open(filename, 'w') as file:
        await file.write()
        ...

def check_timezone(tz:str):
    sign = tz[0]
    if not sign == "+" or sign == "-":
        raise ValueError(f"Inappropriate timezone value given: {tz}")
    offset = tz.split(":")
    try:
        h, m = (map(int, offset))
    except:
        raise ValueError(f"Inappropriate timezone value given: {tz}")
    return h, m


class Weekdays(int, Enum):
    Mon = 0
    Tue = 1
    Wed = 2
    Thu = 3
    Fri = 4
    Sat = 5
    Sun = 6


class TimezoneChoices(str, Enum):
    US_ALASKA = "UTC-09:00"
    US_LOS_ANGELES = "UTC-08:00"
    US_MEXICO = "UTC-06:00"
    US_NEW_YORK = "UTC-05:00"
    US_WASHINGTON_DC = "UTC-03:00"
    EU_LONDON = EU_REYKJAVIK = "UTC+00:00"
    EU_PARIS = "UTC+01:00"
    ASIA_DUBAI = "UTC+04:00"
    ASIA_INDIA = "UTC+05:30"
    ASIA_JAKARTA = "UTC+07:00"
    ASIA_BEIJING = ASIA_KUALA_LUMPUR = \
    ASIA_SINGAPORE = ASIA_MANILA = "UTC+08:00"
    ASIA_SEOUL = ASIA_TOKYO = "UTC+09:00"
    AU_QUEENSLAND = "UTC+10:00"
    NEW_ZEALAND = "UTC+12:00"


class MyModal(disnake.ui.Modal):
    def __init__(self, inter:disnake.AppCmdInter):
        # The details of the modal, and its components
        components = [
            disnake.ui.TextInput(
                label="Timezone in UTC, defaults to UTC+00",
                placeholder=f"e.g. UTC+04 or UTC-02",
                custom_id="tzinfo",
                style=disnake.TextInputStyle.short,
                min_length=6,
                max_length=6,
            ),
            disnake.ui.TextInput(
                label="Schedule details",
                value="**Mon**\nSleep\n\n**Tue**\nSleep\n\n"
                      "**Wed**\nSleep\n\n**Thu**\nSleep\n\n"
                      "**Fri**\nSleep\n\n**Sat**\nSleep\n\n"
                      "**Sun**\nSleep""",
                custom_id="details",
                style=disnake.TextInputStyle.paragraph,
                min_length=1,
            ) 
        ]

        super().__init__(
            title="Create Schedule",
            custom_id="create",
            components=components,
        )

    # The callback received when the user input is completed.
    async def callback(self, inter: disnake.ModalInteraction):
        embed = disnake.Embed(title="Schedule")

        data = inter.text_values
        data = data["details"].split()
        print(data)

        for key, value in data.items():
            embed.add_field(
                name=key.capitalize(),
                value=value[:1024],
                inline=False,
            )
        # result = await DATABASE.insert_many([

        # ])
        await inter.response.send_message(embed=embed)