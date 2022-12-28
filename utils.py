from enum import Enum
import disnake
from Schema import Schema, ObjectId
import random, time, string
from tm import Time, Timezone
from database import DATABASE


def random_time():
    return int(time.time() + random.randint(120, 3600))


def random_seconds(start, stop):
    return random.randrange(start, stop)


def create_random_Schema(once=True):
    t = random_time()
    return Schema(
        user=random.randint(100000000000000000, 999999999999999999),
        details="".join(
            [
                random.choice(list(string.ascii_letters))
                for _ in range(random.randint(10, 48))
            ]
        ),
        timezone="UTC" + random.choice("+-") + str(random.randint(0, 23)),
        time=Time.from_seconds(t),
        once=once,
    )


def format_schedule(time, details) -> str:
    return f"{time} - {details}\n"


def format_task(time, details, completed) -> str:
    return "{2} {0} - {1}\n".format(time, details, "🟢" if completed else "🔴")


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
    ASIA_BEIJING = ASIA_KUALA_LUMPUR = ASIA_SINGAPORE = ASIA_MANILA = "UTC+08:00"
    ASIA_SEOUL = ASIA_TOKYO = "UTC+09:00"
    AU_QUEENSLAND = "UTC+10:00"
    NEW_ZEALAND = "UTC+12:00"


class View(disnake.ui.View):
    def __init__(self, worker):
        self._worker = worker
        super().__init__(timeout=90)

    @disnake.ui.string_select(
        placeholder="Available actions.",
        options=[
            disnake.SelectOption(label="Create New Task", value="create"),
            # disnake.SelectOption(label="Edit Task", value="edittask"),
            # disnake.SelectOption(label="Cancel Task", value="deletetask"),
            # disnake.SelectOption(label="Edit Schedule", value="editschedule"),
            # disnake.SelectOption(label="Cancel Schedule", value="deleteschedule"),
        ],
    )
    async def callback(
        self, option: disnake.ui.StringSelect, inter: disnake.AppCmdInter
    ):
        match option.values[0]:
            case "create":
                await inter.response.send_modal(CreateModal())

            case "edittask" | "canceltask":
                await inter.response.defer(with_message=False)
                tasklist = await DATABASE.find(
                    {"user": inter.author.id, "once": True}
                ).to_list(25)

                return await inter.edit_original_response(
                    view=self.add_item(Select(option.values[0][:-4], tasklist, self._worker))
                )
            case "editschedule" | "cancelschedule":
                await inter.response.defer(with_message=False)
                tasklist = await DATABASE.find(
                    {"user": inter.author.id, "once": False}
                ).to_list(25)

                return await inter.edit_original_response(
                    view=self.add_item(Select(option.values[0][:-8], tasklist, self._worker))
                )


class Select(disnake.ui.StringSelect):
    def __init__(self, type: str, lists: list[dict[Schema]], worker):
        self._worker = worker
        self._lists = lists
        super().__init__(
            options=[
                disnake.SelectOption(
                    label=format_schedule(i["time"], i["details"]), value=str(n)
                )
                for n, i in enumerate(lists)
            ]
            or ["None"],
            custom_id=type,
            max_values=1 if type == "edit" else len(lists),
            placeholder=f"Select to {type}.",
        )

    async def callback(self, interaction: disnake.AppCmdInter):
        self._lists = [self._lists[i] for i in map(int, self.values)]

        match self.custom_id:
            case "edit":
                return await interaction.response.send_modal(
                    EditModal(self._lists[0], self._worker))

            case "cancel":
                self._worker.cancel(self._lists)
                res = await DATABASE.delete_many(
                    {"_id": {"$in": [i["_id"] for i in self._lists]}}
                )
                return await interaction.response.send_message(
                    f"Successfully cancelled {res.deleted_count} tasks.", ephemeral=True
                )


class EditModal(disnake.ui.Modal):
    def __init__(self, data, worker):
        self._data = data
        self._worker = worker
        super().__init__(
            title="Edit",
            custom_id="edit",
            timeout=60,
            components=[
                disnake.ui.TextInput(
                    label="Detail",
                    custom_id="Detail",
                    style=disnake.TextInputStyle.paragraph,
                    min_length=1,
                    max_length=48,
                )
            ],
        )

    async def edit(self, inter: disnake.ModalInteraction):
        new = self._data.copy()
        new.update({"details": inter.text_values["Detail"]})

        await DATABASE.update_one(self.data, new)

        self._worker.edit(self._data, new)
        await inter.response.send_message("Successfully edited.")


class CreateModal(disnake.ui.Modal):
    def __init__(self, worker):
        self._worker = worker
        super().__init__(
            title="Create",
            components=[
                disnake.ui.TextInput(
                    label="Timezone in UTC, e.g. UTC+5:30",
                    custom_id="Timezone",
                    value="UTC+00:00",
                    style=disnake.TextInputStyle.short,
                    min_length=9,
                    max_length=9,
                ),
                disnake.ui.TextInput(
                    label='Date (YYYY/MM/DD or MM/DD) or "today"',
                    custom_id="Date",
                    style=disnake.TextInputStyle.short,
                    min_length=3,
                    max_length=10,
                ),
                disnake.ui.TextInput(
                    label="Time (H:M:S or H:M)",
                    custom_id="Time",
                    style=disnake.TextInputStyle.short,
                    min_length=5,
                    max_length=8,
                ),
                disnake.ui.TextInput(
                    label="Details",
                    custom_id="Details",
                    style=disnake.TextInputStyle.paragraph,
                    min_length=1,
                    max_length=48,
                ),
            ],
        )

    async def callback(self, inter: disnake.ModalInteraction):
        try:
            data = Schema(
                user=inter.author.id,
                timezone=inter.text_values["Timezone"],
                date=inter.text_values["Date"],
                time=inter.text_values["Time"],
                details=inter.text_values["Details"],
                once=True,
            )
        except Exception as e:
            return await inter.response.send_message(e, ephemeral=True)
        else:
            await DATABASE.insert_one(data.to_db())
            self._worker.check(data.to_db())

            return await inter.response.send_message(
                "Successfully created.", ephemeral=True
            )
