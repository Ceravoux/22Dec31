"""
/invoke cmd
set
{
    name,
    tz,
    details: {Time(wed, 1pm): "sleep"}
}


t = calc time
handle = loop.call_later(t, callback)
XXX how to refer to handle after function ends??

push time to db
run the closest to now (1)
store unique id (authorid) along with details
keep the handle and sleep until time

in case of cancel: 
-> cancel sleep 
-> delete data from db
-> get next closest time and sleep

in case of a new data being pushed to db
and data < current_sleep:
-> cancel sleep 
-> don't delete data from db
-> change time

for datas where once is false:
-> update data?

to start loop:
-> when a data is pushed into db, call 
   db.get(data) and run, but if it is sleeping, wait later
"""
#XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
"""
how to get closest `time from now` from db?
1. get all data (in str) and create time instances then sort
    downside: what if there are too many datas to sort?
              inefficient to instantiate new classes (?)

2. create 7 collections based on weekdays and find data based on today
    downside: what if there are no datas to be run today?

3. change the time field to separate fields -- y m d h m s tz o
   and we can use aggregration (maybe) to get the cloest time
   e.g. $min on all fields

4. include new field posix_time (bigint) and get data with $min
"""

"""
when function is awaiting on a future, but another data that runs earlier comes in
e.g.
future awaiting for 18:30:50
new data is 18:30:20
cancel sleep
new sleep for 18:30:20

more new data 18:30:15
cancel sleep
...

"""

import pytz, datetime, asyncio, enum
from motor.motor_asyncio import AsyncIOMotorClient
from tm import Time, Timezone
from os import getenv
from dotenv import load_dotenv
load_dotenv()

class Tz(str, enum.Enum):
    US_ALASKA = "-09:00"
    LOS_ANGELES = "-08:00"
    US_MEXICO = "-06:00"
    US_NEW_YORK = "-05:00"
    US_WASHINGTON_DC = "-03:00"
    EU_LONDON = EU_REYKJAVIK = "+00:00"
    EU_PARIS = "+01:00"
    ASIA_DUBAI = "+04:00"
    ASIA_INDIA = "+05:30"
    ASIA_JAKARTA = "+07:00"
    ASIA_BEIJING = ASIA_KUALA_LUMPUR = \
    ASIA_SINGAPORE = ASIA_MANILA = "+08:00"
    ASIA_SEOUL = ASIA_TOKYO = "+09:00"
    AU_QUEENSLAND = "+10:00"
    NEW_ZEALAND = "+12:00"

client = AsyncIOMotorClient(getenv("DB_KEY"), serverSelectionTimeoutMS=5000)
try:
    DATABASE = client["project"]["project02"]
except Exception as e:
    print(f"{e}: Unable to connect to the server.")
pacific = pytz.timezone('US/Pacific')

t = Time.now(tz=Timezone(*map(int, Tz.ASIA_JAKARTA.split(":"))))
# t = datetime.datetime(2002, 10, 27, 6, 0, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=7)))
# t = tea(2002, 10, 27, 6, 0, 0)

# aware_datetime = pacific.localize(t)
# print(aware_datetime)

async def main():
    
    await DATABASE.insert_one({"time":t})
    print([i async for i in DATABASE.find({"time":t})])
    print(await DATABASE.count_documents({}))

asyncio.run(main())