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

import asyncio

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

async def main(t):
    sleep = loop.create_future()
    loop.call_later(t, sleep.set_result, 1)
    await sleep
    print("1")
    return t

f = asyncio.gather(main(5), main(20), main(-1))
loop.run_until_complete(f)
print(f)


"""
Today, many have been preoccupied with the preparation of 
welcoming christmas, be it the tree, decorations, food, etc.
Despite all that, for most people, the best part about christmas 
is the gifts. 
Gifts are a concrete way of sharing joy and happiness, at least 
the way I see it. But what makes them so appealing?
We believe that the answer is the presentation of the gift itself;
the wrapping. A nice looking gift gives off a good sense of 
curiosity and expectation to many: 
"What could be inside lies inside those fleshing, 
sweet and colourful layers of paper?"
Thus today, we are here to share and teach...
"""
