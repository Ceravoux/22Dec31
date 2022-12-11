class Schema:
    """
    {
        user: 1234567890,

        details: "sleep",

        timezone: "UTC+00",

        time: "Sunday, 27 November 2022 08:00 UTC+00",

        posix_time: 1234567890,
    }
    """
    def __init__(
        self, user: int = ..., details: str = ..., timezone: str = ..., time: str = ..., once: bool = False, posix_time: int = ...
    ) -> None:
        if not isinstance(details, str):
            raise ValueError(
                f"Schema(): ``name`` must be str, not {type(details).__name__!r}"
            )
        if not isinstance(user, int):
            raise ValueError(
                f"Schema(): ``user`` must be int, not {type(user).__name__!r}"
            )
        if not isinstance(time, str):
            raise ValueError(
                f"Schema(): ``schedule`` must be str, not {type(time).__name__!r}"
            )
        if not isinstance(once, bool):
            raise ValueError(
                f"Schema(): ``once`` must be str, not {type(once).__name__!r}"
            )
        if not isinstance(posix_time, (int, float)):
            raise ValueError(
                f"Schema(): ``posix_time`` must be int, not {type(posix_time).__name__!r}"
            )

        self.user = user
        self.details = details
        self.timezone = timezone
        self.time = time
        self.once = once
        self.posix_time = posix_time

    def __str__(self):
        return str(self.__dict__)

    @classmethod
    def from_str(cls, s:str):
        s = s.split()

        return cls()



