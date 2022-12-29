import disnake
from schema import Schema, ObjectId
from database import database
from instances import worker


class View(disnake.ui.View):
    def __init__(
        self,
        task: list[tuple[ObjectId, str]],
        schedule: list[tuple[ObjectId, str]],
    ):
        super().__init__(timeout=90)
        self.task = task
        self.sched = schedule

        if task:
            self.children[0].append_option(
                disnake.SelectOption(label="Edit Task", value="edittask")
            )
            self.children[0].append_option(
                disnake.SelectOption(label="Cancel Task", value="canceltask")
            )
        if schedule:
            self.children[0].append_option(
                disnake.SelectOption(label="Edit Schedule", value="editschedule")
            )
            self.children[0].append_option(
                disnake.SelectOption(label="Cancel Schedule", value="cancelschedule")
            )

    @disnake.ui.string_select(
        placeholder="Available actions.",
        options=[disnake.SelectOption(label="Create New Task", value="create")],
    )
    async def callback(
        self, option: disnake.ui.StringSelect, inter: disnake.AppCmdInter
    ):
        match option.values[0]:
            case "create":
                await inter.response.send_modal(CreateModal())

            case "edittask" | "canceltask":
                await inter.response.defer(with_message=False)
                return await inter.edit_original_response(
                    view=self.add_item(Select(option.values[0][:-4], self.task))
                )
            case "editschedule" | "cancelschedule":
                await inter.response.defer(with_message=False)
                return await inter.edit_original_response(
                    view=self.add_item(Select(option.values[0][:-8], self.sched))
                )


class Select(disnake.ui.StringSelect):
    def __init__(self, type: str, lists: list[tuple[ObjectId, str]]):
        super().__init__(
            options=[disnake.SelectOption(label=i[1], value=str(i[0])) for i in lists],
            custom_id=type,
            max_values=1 if type == "edit" else len(lists),
            placeholder=f"Select to {type}.",
        )

    async def callback(self, interaction: disnake.AppCmdInter):
        match self.custom_id:
            case "edit":
                return await interaction.response.send_modal(EditModal(self.values[0]))
            case "cancel":
                for i in self.values:
                    res = await database.find_one_and_delete({"_id": ObjectId(i)})
                    worker.cancel(res)

                return await interaction.response.send_message(
                    f"Successfully cancelled {len(self.values)} task(s).", ephemeral=True
                )


class EditModal(disnake.ui.Modal):
    def __init__(self, _id):
        super().__init__(
            title="Edit",
            custom_id=_id,
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

    async def callback(self, inter: disnake.ModalInteraction):
        res = await database.find_one_and_update(
            {"_id": ObjectId(self.custom_id)},
            {"$set": {"details": inter.text_values["Detail"]}},
        )
        new = res.copy()
        new.update({"details":inter.text_values["Detail"]})

        worker.edit(res, new)
        await inter.response.send_message("Successfully edited.", ephemeral=True)


class CreateModal(disnake.ui.Modal):
    def __init__(self):
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
            await database.insert_one(data.to_db())
            worker.check(data.to_db())
            return await inter.response.send_message(
                "Successfully created.", ephemeral=True
            )
