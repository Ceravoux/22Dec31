from tm import Time, Timezone, check_date, check_time, check_timezone, TIME_LIMIT
from bson.objectid import ObjectId


class Schema:
    """
    Creates a complete schema from user, details and time field.

    {
        _id: ObjectId(12byte),
        user: 123456789012345678
        details: "sleep",
        timezone: "UTC+00",
        time: Time(2022, 12, 17, 17, 54, 9, tzinfo=Timezone())
        posix_time: 1234567890,
        once: True
        complete: False
    }
    """

    def __init__(
        self,
        *,
        user: int = ...,
        timezone: str = ...,
        weekday: int = ...,
        date: str = ...,
        time: str = ...,
        details: str = ...,
        once: bool = ...,
    ) -> None:
        if not isinstance(details, str):
            raise ValueError(
                f"Schema(): ``details`` must be str, not {type(details).__name__!r}"
            )
        if not isinstance(user, int):
            raise ValueError(
                f"Schema(): ``userid`` must be int, not {type(user).__name__!r}"
            )
        if not isinstance(timezone, str):
            raise ValueError(
                f"Schema(): ``timezone`` must be str, not {type(timezone).__name__!r}"
            )
        if not isinstance(time, str):
            raise ValueError(
                f"Schema(): ``time`` must be str, not {type(time).__name__!r}"
            )
        if not isinstance(once, bool):
            raise ValueError(
                f"Schema(): ``once`` must be str, not {type(once).__name__!r}"
            )
        if (not isinstance(weekday, int)) and once is False:
            raise ValueError(
                f"Schema(): ``weekday`` must be int or weekday is specified, but ``once`` is not False."
            )
        if (not isinstance(date, str)) and once is True:
            raise ValueError(
                f"Schema(): ``date`` must be str or date is specified, but ``once`` is not True."
            )

        try:
            self.timezone = check_timezone(timezone)

            now = Time.now()
            max = Time.from_seconds(now.to_seconds() + TIME_LIMIT * 86400)

            time = check_time(time)
            if once:
                date = check_date(date, (now.year, now.month, now.day))
                self.time = Time(
                    *date, 
                    *time, 
                    tzinfo=Timezone.from_string_offset(self.timezone)
                )
            else:
                self.time = Time.from_weekday(
                    weekday, 
                    *time, 
                    tzinfo=Timezone.from_string_offset(self.timezone)
                )

            assert now < self.time - self.time.utcoffset() < max, \
                f"Time must be within {now} and {max}"
        
        except Exception as e:
            raise e

        self._id = ObjectId()
        self.user = user
        self.details = details
        self.once = once
        self.posix_time = self.time.to_seconds()

        # whether the task is completed
        self.completed = False

    def to_db(self):
        return self.__dict__
