"""It has been done."""

__all__ = ("Time", "Timezone")

from datetime import tzinfo, datetime, timedelta
from time import gmtime, time
from enum import Enum

SECONDS_IN_1D = 24 * 3600
SECONDS_IN_1W = SECONDS_IN_1D * 7

TIME_LIMIT = 183

class Weekdays(int, Enum):
    Mon = 0
    Tue = 1
    Wed = 2
    Thu = 3
    Fri = 4
    Sat = 5
    Sun = 6

DAYS_IN_MONTHS = [
    0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31,
]

def _isleap(year):
    return True if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else False

def _ymd1_to_ymd2_in_days(ymd1, ymd2, *, within_time_limit=False) -> int:
    func = lambda y: y * 365 + y // 4 - y // 100 + y // 400
    days = func(ymd2[0]) - func(ymd1[0])
    if ymd2[1] < ymd1[1]:
        days -= sum(DAYS_IN_MONTHS[ymd2[1] : ymd1[1]])
    else:
        days += sum(DAYS_IN_MONTHS[ymd1[1] : ymd2[1]])

    if (_isleap(ymd1[0]) and ymd1[1] < 2 and ymd2[1] > 2) or (
        _isleap(ymd2[0]) and ymd2[1] > 2
    ):
        days += 1
    days -= ymd1[2]
    days += ymd2[2]

    if within_time_limit and days > TIME_LIMIT:
        raise ValueError(f"Exceeded time limit (183 days) {ymd2}")

    return days

def check_time(t: str) -> tuple[int]:
    t = t.split(":")
    try:
        hms = tuple(map(int, t))
        l = len(hms)
        if l > 3 or l < 1:
            raise ValueError("time must be in hour:minute:second or hour:minute")
        if l > 0 and not 0 <= hms[0] <= 23:
            raise ValueError("Hour must be 0-23")
        if l > 1 and not 0 <= hms[1] <= 59:
            raise ValueError("Minute must be 0-59")
        if l > 2 and not 0 <= hms[2] <= 59:
            raise ValueError("Second must be 0-59")

    except Exception as e:
        raise ValueError(f"Inappropriate time given: {t}. {e.args}")
    return hms

def check_date(d: str, today: tuple[int]) -> tuple[int]:
    if d.strip().lower() == "today":
        return today

    d = d.split("/")
    try:
        ymd = tuple(map(int, d))
        l = len(ymd)
        if l > 3 or l < 2:
            raise ValueError("Date must be in year/month/day or month/day")

        if l == 2:
            ymd = (today[0],) + ymd

        # if not 1 <= ymd[0] < 9999:
        #     raise ValueError("Year")

        # if not 1 <= ymd[1] <= 12:
        #     raise ValueError(f"Month must be in 1-12, not {ymd[1]}")

        # if (_isleap(ymd[0]) and ymd[1] == 2 and not 1 <= ymd[2] <= 29) or (
        #     not 1 <= ymd[2] <= DAYS_IN_MONTHS[ymd[1]]
        # ):
        #     ValueError(f"Day exceeds days in month")

    except Exception as e:
        raise ValueError(f"Inappropriate date given: {d}. {e.args}")

def check_timezone(tz: str) -> str:
    if tz[:3] != "UTC":
        raise ValueError(f"Timezone must be in UTC, not {tz[:3]}")
    sign = tz[3]
    if not sign == "+" or sign == "-":
        raise ValueError(f"Inappropriate timezone offset given: {tz}")
    check_time(tz[4:])
    return tz


class Time(datetime):
    """
    Simple class that supports time and date 
    (except DST). This class has also included
    a variable `once` for disposal purposes.

    Parameters
    ---------------
    year: int
    month: int 
    day: int 
    hour: int 
    minute: int 
    second: int 
    tzinfo: Timezone
    
    `once` can only be set to True with run_once(),
    defaults to False.
    """

    __slots__ = '_year', '_month', '_day', '_hour', '_minute', '_second', '_microsecond', '_tzinfo', '_hashcode', '_fold', '_once'

    def __new__(
        cls,
        year: int = 1,
        month: int = 1,
        day: int = 1,
        hour: int = 0,
        minute: int = 0,
        second: int = 0,
        *args,
        tzinfo: "Timezone" = None,
    ) -> "Time":
        """
        Constructor.

        Args:
            weekday, hour, minute, second: default to zero
            tzinfo: default to UTC+00
        """

        self = super().__new__(
            cls, 
            year=year, 
            month=month, 
            day=day, 
            hour=hour, 
            minute=minute,
            second=second,
            tzinfo=tzinfo or Timezone(),
            microsecond=0
        )

        self._once = False
        return self

    @property
    def once(self) -> str:
        """whether it should be disposed right away after used"""
        return self._once

    @property
    def weekday(self) -> str:
        return Weekdays(super().weekday()).name

    def run_once(self):
        self._once = True

    def __str__(self):
        return f"{self.weekday}, {self.year:04d}/{self.month:02d}/{self.day:02d} {self.hour:02d}:{self.minute:02d}:{self.second:02d} {self.tzinfo}"

    def __repr__(self):
        return f"{type(self).__name__}({self.year}, {self.month}, {self.day}, {self.hour}, {self.minute}, {self.second}, {self.tzinfo}, once={self.once})"
    
    def __eq__(self, other):
        if isinstance(other, datetime):
            other = other.replace(microsecond=0)
        return super().__eq__(other)

    def __le__(self, other):
        if isinstance(other, datetime):
            other = other.replace(microsecond=0)
        return super().__le__(other)

    def __lt__(self, other):
        if isinstance(other, datetime):
            other = other.replace(microsecond=0)
        return super().__lt__(other)

    def __ge__(self, other):
        if isinstance(other, datetime):
            other = other.replace(microsecond=0)
        return super().__ge__(other)

    def __gt__(self, other):
        if isinstance(other, datetime):
            other = other.replace(microsecond=0)
        return super().__gt__(other)

    def __hash__(self):
        return super().__hash__()

    def to_seconds(self):
        """returns seconds since unix epoch"""
        return (
            _ymd1_to_ymd2_in_days(
                (1970, 1, 1), (self.year, self.month, self.day), within_time_limit=False
            )
            * SECONDS_IN_1D
            + self.hour * 3600
            + self.minute * 60
            + self.second
        )

    @classmethod
    def now(cls, tz: "Timezone" = None):
        """
        Constructs a `Time` from the current POSIX timestamp 
        (like time.time()), and adjusts accordingly with the 
        given timezone (defaults to UTC+0).
        """
        if tz is None:
            tz = Timezone()
        return cls.from_seconds(time() + tz.utcoffset().total_seconds(), tzinfo=tz)
    
    @classmethod
    def utcnow(cls):
        return cls.now()

    @classmethod
    def from_seconds(cls, seconds: int, *, tzinfo: "Timezone"=None):
        """
        Constructs a `Time` from seconds from POSIX timestamp 
        (like time.time())
        """
        year, month, day, hour, minute, second = gmtime(seconds)[:6]
        return cls(year, month, day, hour, minute, second, tzinfo=tzinfo)

    @classmethod
    def from_weekday(cls, weekday: int, hour=0, minute=0, second=0, *, tzinfo: "Timezone"=None):
        if not 0 <= weekday <= 6:
            raise ValueError("weekday is not within 0 and 6 inclusive")
        
        now = cls.now(tzinfo)
        today = Weekdays[now.weekday].value
        return cls.from_seconds(
            now.to_seconds() 
            + (weekday - today + (7 if weekday < today or (weekday == today and hour < now.hour) else 0)) * SECONDS_IN_1D
            + (hour - now.hour) * 3600
            + (minute - now.minute) * 60
            + second - now.second,
            tzinfo=tzinfo
        )

    def to_next_week(self):
        return self.from_seconds(self.to_seconds() + SECONDS_IN_1W, tzinfo=self.tzinfo)

    def to_seconds_from_now(self):
        """returns the total seconds between now and self"""
        now = self.now(self.tzinfo)
        if self >= now:
            return (self - now).total_seconds()
        raise ValueError(f"self is lesser than now, expected {self} to be >= {now}")

    def replace(
        self,
        *,
        year: int = None,
        month: int = None,
        day: int = None,
        hour: int = None,
        minute: int = None,
        second: int = None,
        microsecond = 0,
        tzinfo: "Timezone" = True,
    ):
        return type(self)(
            year or self.year,
            month or self.month,
            day or self.day,
            hour or self.hour,
            minute or self.minute,
            second or self.second,
            tzinfo=self.tzinfo if tzinfo == True else tzinfo,
        )

class _Time:
    """
    Simple class that supports time and date 
    (except DST). This class has also included
    a variable `once` for disposal purposes.

    Parameters
    ---------------
    year: int
    month: int 
    day: int 
    hour: int 
    minute: int 
    second: int 
    tzinfo: Timezone
    
    `once` can only be set to True with run_once(),
    defaults to False.
    """

    __slots__ = (
        "_year", "_month", "_day", "_hour", "_minute", "_second", "_once", "_tzinfo"
    )

    def __new__(
        cls,
        year: int = 1,
        month: int = 1,
        day: int = 1,
        hour: int = 0,
        minute: int = 0,
        second: int = 0,
        *,
        tzinfo: "Timezone" = None,
    ) -> "Time":
        """
        Constructor.

        Args:
            weekday, hour, minute, second: default to zero
            tzinfo: default to UTC+00
        """

        if not 1 <= year:
            ...
        if not 1 <= month <= 12:
            ...
        if not 1 <= day <= DAYS_IN_MONTHS[month]:
            ... #leap year check
        if not 0 <= hour <= 23:
            ...
        if not 0 <= minute <= 59:
            ...
        if not 0 <= second <= 59:
            ...
            
        self = super().__new__(cls)
        self._year = year
        self._month = month
        self._day = day
        self._hour = hour
        self._minute = minute
        self._second = second
        self._tzinfo = tzinfo or Timezone()
        self._once = False
        return self

    @property
    def year(self) -> int:
        return self._year

    @property
    def month(self) -> int:
        return self._month

    @property
    def day(self) -> int:
        return self._day

    @property
    def hour(self) -> int:
        return self._hour

    @property
    def minute(self) -> int:
        return self._minute

    @property
    def second(self) -> int:
        return self._second

    @property
    def once(self) -> str:
        """whether it should be disposed right away after used"""
        return self._once

    @property
    def tzinfo(self) -> "Timezone":
        """timezone"""
        return self._tzinfo

    @property
    def weekday(self):
        return Weekdays(
            _ymd1_to_ymd2_in_days(
                (1, 1, 1), (self.year, self.month, self.day), within_time_limit=False
            ) % 7
        ).name

    def run_once(self):
        self._once = True

    def __str__(self):
        return f"{self.weekday}, {self.year:04d}/{self.month:02d}/{self.day:02d} {self.hour:02d}:{self.minute:02d}:{self.second:02d} {self.tzinfo}"

    def __repr__(self):
        return f"{type(self).__name__}({self.year}, {self.month}, {self.day}, {self.hour}, {self.minute}, {self.second}, {self.tzinfo}, once={self.once})"

    def __eq__(self, other):
        if isinstance(other, Time):
            if self.tzinfo == other.tzinfo:
                return all(
                    getattr(self, n) == getattr(other, n) for n in self.__slots__[:-2]
                ) 
            raise ValueError(f"Different tzinfo; expected {self.tzinfo} given {other.tzinfo}")
        raise TypeError(
            f"expected type `Time`, given {type(other).__class__.__name__!r}"
        )

    def __ge__(self, other):
        if isinstance(other, Time):
            if self.tzinfo == other.tzinfo:
                return any(
                    getattr(self, n) >= getattr(other, n) for n in self.__slots__[:-2]
                )
            raise ValueError(f"Different tzinfo; expected {self.tzinfo} given {other.tzinfo}")
        raise TypeError(
            f"expected type `Time`, given {type(other).__class__.__name__!r}"
        )

    def __le__(self, other):
        if isinstance(other, Time):
            if self.tzinfo == other.tzinfo:
                return any(
                    getattr(self, n) <= getattr(other, n) for n in self.__slots__[:-2]
                )
            raise ValueError(f"Different tzinfo; expected {self.tzinfo} given {other.tzinfo}")
        raise TypeError(
            f"expected type `Time`, given {type(other).__class__.__name__!r}"
        )

    def __gt__(self, other):
        if isinstance(other, Time):
            if self.tzinfo == other.tzinfo:
                return any(getattr(self, n) > getattr(other, n) for n in self.__slots__[:-2])
            
            raise ValueError(f"Different tzinfo; expected {self.tzinfo} given {other.tzinfo}")
        raise TypeError(
            f"expected type `Time`, given {type(other).__class__.__name__!r}"
        )

    def __lt__(self, other):
        if isinstance(other, Time):
            if self.tzinfo == other.tzinfo:
                return any(getattr(self, n) < getattr(other, n) for n in self.__slots__[:-2])
            raise ValueError(f"Different tzinfo; expected {self.tzinfo} given {other.tzinfo}")
        raise TypeError(
            f"expected type `Time`, given {type(other).__class__.__name__!r}"
        )

    def to_seconds(self):
        return (
            _ymd1_to_ymd2_in_days(
                (1970, 1, 1), (self.year, self.month, self.day), within_time_limit=False
            )
            * SECONDS_IN_1D
            + self.hour * 3600
            + self.minute * 60
            + self.second
        )

    @classmethod
    def now(cls, tz: "Timezone" = None):
        """
        Constructs a `Time` from the current POSIX timestamp 
        (like time.time()), and adjusts accordingly with the 
        given timezone (defaults to UTC+0).
        """
        if tz is None:
            tz = Timezone()
        return cls.from_seconds(time() + tz.utcoffset(in_seconds=True), tzinfo=tz)

    @classmethod
    def from_seconds(cls, seconds: int, *, tzinfo: "Timezone"=None):
        """
        Constructs a `Time` from seconds from POSIX timestamp 
        (like time.time())
        """
        year, month, day, hour, minute, second = gmtime(seconds)[:6]
        return cls(year, month, day, hour, minute, second, tzinfo=tzinfo)

    @classmethod
    def from_weekday(cls, weekday: int, hour=0, minute=0, second=0, *, tzinfo: "Timezone"=None):
        
        now = cls.now(tzinfo)
        today = Weekdays[now.weekday].value

        return cls.from_seconds(
            now.to_seconds() 
            + (weekday - today + (7 if weekday < today else 0)) * SECONDS_IN_1D
            + hour * 3600
            + minute * 60
            + second,
            tzinfo=tzinfo
        )

    def to_next_week(self):
        return self.from_seconds(self.to_seconds() + SECONDS_IN_1W, tzinfo=self._tzinfo)

    def to_seconds_from_now(self):
        """returns the total seconds between now and self"""
        now = self.now(self.tzinfo)
        if self > now:
            o = _ymd1_to_ymd2_in_days((now.year, now.month, now.day), (self.year, self.month, self.day), within_time_limit=True) * SECONDS_IN_1D
            res = (o
                + (self.hour * 3600 + self.minute * 60 + self.second) 
                - (now.hour * 3600 + now.minute * 60 + now.second)
            )
            return res
        raise ValueError("self is lesser than now, expected self to be > now")

    def replace(
        self,
        *,
        year: int = None,
        month: int = None,
        day: int = None,
        hour: int = None,
        minute: int = None,
        second: int = None,
        tzinfo: "Timezone" = None,
    ):
        return type(self)(
            year or self.year,
            month or self.month,
            day or self.day,
            hour or self.hour,
            minute or self.minute,
            second or self.second,
            tzinfo or self.tzinfo,
        )

class Timezone(tzinfo):
    def __init__(self, hour=0, minute=0) -> None:
        if not isinstance(hour, int):
            raise TypeError(f"hour must be `int`, given {type(hour).__name__!r}")
        if not isinstance(minute, int):
            raise TypeError(f"minute must be `int`, given {type(minute).__name__!r}")
        if not -23 <= hour <= 23:
            raise
        if not -59 <= minute <= 59:
            raise
        if hour < 0 and minute < 0:
            raise
        if minute < 0 and hour != 0:
            raise

        self._hour = hour
        self._minute = minute

    @property
    def minute(self) -> int:
        return self._minute

    @property
    def hour(self) -> int:
        return self._hour

    def __eq__(self, other):
        if isinstance(other, Timezone):
            return self._hour == other._hour and self._minute == other._minute
        return TypeError(f"expected other as type `Timezone`, not {other.__class__.__name__!r}")

    def __str__(self):
        return Timezone.name_from_offset(self)

    @classmethod
    def from_string_offset(cls, offset:str):
        """
        Creates a `Timezone` instance from UTC offset.
        e.g. 'UTC+09:00'
        """

        if not offset:
            return cls()

        if offset[:3] != "UTC":
            raise ValueError("from_string_offset(): offset not in UTC")

        return cls(*map(int, offset[3:].split(":")))

    @staticmethod
    def name_from_offset(tz):
        if not isinstance(tz, Timezone):
            raise TypeError(
                f"name_from_offset() expected `Timezone` instance, given {type(tz).__class__.__name__!r}"
            )

        if tz._hour < 0 or tz._minute < 0:
            sign = "-"
        else:
            sign = "+"

        return f"UTC{sign}{tz._hour:02d}:{tz._minute:02d}"

    def utcoffset(self, t=None):
        if isinstance(t, Time) or t is None:
            return timedelta(hours=self._hour, minutes=self._minute)

    def fromutc(self, t: "Time"):
        "changes the time to follow the offset"
        if isinstance(t, Time):
            if t.tzinfo is not self:
                # if the time has different timezone
                raise ValueError("fromutc: dt.tzinfo is not self")
            return t + self.utcoffset()
        raise TypeError(f"fromutc(): expected Time, given {type(t).__class__.__name__!r}")

class _Timezone(tzinfo):
    def __init__(self, hour=0, minute=0) -> None:
        if not isinstance(hour, int):
            raise TypeError(f"minute must be `int`, given {type(hour).__name__!r}")
        if not isinstance(minute, int):
            raise TypeError(f"minute must be `int`, given {type(minute).__name__!r}")
        if not -23 <= hour <= 23:
            raise
        if not -59 <= minute <= 59:
            raise
        if hour < 0 and minute < 0:
            raise
        if minute < 0 and hour != 0:
            raise

        self._hour = hour
        self._minute = minute

    @property
    def minute(self) -> int:
        return self._minute

    @property
    def hour(self) -> int:
        return self._hour

    def __eq__(self, other):
        if isinstance(other, Timezone):
            return self._hour == other._hour and self._minute == other._minute
        return TypeError(f"expected other as type `Timezone`, not {other.__class__.__name__!r}")

    def __str__(self):
        return Timezone.name_from_offset(self)

    @classmethod
    def from_offset(cls, offset:str):

        return cls(int(offset))

    @staticmethod
    def name_from_offset(tz):
        if not isinstance(tz, Timezone):
            raise TypeError(
                f"name_from_offset() expected `Timezone` instance, given {type(tz).__class__.__name__!r}"
            )

        if tz._hour < 0 or tz._minute < 0:
            sign = "-"
        else:
            sign = "+"

        return f"UTC{sign}{tz._hour:02d}:{tz._minute:02d}"

    def utcoffset(self, *, in_seconds=False):
        return (
            (self._hour * 3600 + self._minute * 60)
            if in_seconds
            else (self._hour, self._minute)
        )

    def fromutc(self, t: "Time"):
        "changes the time to follow the offset"
        if isinstance(t, Time):
            if t.tzinfo is not self:
                # if the time has different timezone
                raise ValueError("fromutc: dt.tzinfo is not self")

            return type(t).from_seconds(
                t.to_seconds() + self.utcoffset(in_seconds=True), tzinfo=self
            )
        raise TypeError("Expected Time instance")
