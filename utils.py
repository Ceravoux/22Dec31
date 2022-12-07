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
        userid=random.randint(100000000, 9999999999), 
        details=''.join([random.choice(list(string.ascii_letters)) for _ in range(random.randint(10, 48))]), 
        timezone="UTC"+random.choice("+-")+str(random.randint(0, 23)),
        time="urmom",
        once=True,
        posix_time=time.time() + random.randint(3600, 86400*2)
    )

async def to_csv(data: dict, filename: str):
    if not isinstance(data, dict):
        raise ValueError(f"data has to be ``dict``, provided {type(data)}")

    async with aiofiles.open(filename, 'w') as file:
        
        await file.write()
        ...

def format_to_schedule():
    """
    {
        Monday: [
            {"12:00:00": "do a"},
            {"14:00:00": "do a"},
            {"18:00:00": "do a"},
        ],
        Wednesday: [
            {"12:00:00": "do a"},
            {"14:00:00": "do a"},
            {"18:00:00": "do a"},
        ],
        Sunday: [
            {"12:00:00": "do a"},
            {"14:00:00": "do a"},
            {"18:00:00": "do a"},
        ]
    }
    """

class Weekdays(Enum):
    Mon = 0
    Tue = 1
    Wed = 2
    Thu = 3
    Fri = 4
    Sat = 5
    Sun = 6

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