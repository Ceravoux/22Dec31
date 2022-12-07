class Schema:
    """
    {
        userid: 1234567890,

        details: "sleep",

        timezone: "UTC+00",

        time: "Sunday, 27 November 2022 08:00 UTC+00",

        posix_time: 1234567890,
    }
    """
    def __init__(
        self, userid: int = ..., details: str = ..., timezone: str = ..., time: str = ..., once: bool = False, posix_time: int = ...
    ) -> None:
        if not isinstance(details, str):
            raise ValueError(
                f"Schema(): ``name`` must be str, not {type(details).__name__!r}"
            )
        if not isinstance(userid, int):
            raise ValueError(
                f"Schema(): ``userid`` must be int, not {type(userid).__name__!r}"
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

        self.userid = userid
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



