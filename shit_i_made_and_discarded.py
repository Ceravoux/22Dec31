__all__ = ("ListofTimeSequence", "Loop")


import asyncio
import sys, os
import traceback
from typing import Coroutine
from tm import Time, Timezone

os.environ['PYTHONASYNCIODEBUG'] = '1'

class ListofTimeSequence(list):
    """Inherits from `list`. 
    Helper for `Loop`.
    Contains only values of type `Time`.
    """
    
    def __init__(self, iterable:list, loop_instance:"Loop") -> "ListofTimeSequence":
        assert all(isinstance(i, Time) for i in iterable), \
               "List values must be of type `Time`"
        super().__init__(iterable)
        self.sort()
        self.append = self.extend = self.__setitem__ = property()
        self._loop_instance = loop_instance


    def __getitem__(self, y) -> "Time":
        return super().__getitem__(y)

    def add(self, object):
        # HACK: Implement binary search instead of linear
        for i in range(len(self)):
            print(object)
            if self[i] == object: 
                return

            if self[i] > object:
                self[:] = self[:i] + [object] + self[i:]

                # XXX, when loop.start() is not called, the index
                # gets shifted 
                if self._loop_instance.current_iteration <= i:
                    self._loop_instance.current_iteration += 1
                    self._loop_instance.next_iteration += 1
                break
        else:
            self += [object]
            # XXX INDEXING ERROR when current_iter = last element 
            #                    and next_iter = 0

    def sort(self):
        """sorts list to an ascending order by 
        closest :class:`Time` from :func:`Time.now()`"""
        super().sort(
            key = lambda x: x.to_seconds_from_now())


class Loop:
    # count instances made from db
    
    __slots__ = ("times", "loop", "coro", "current_iteration", 
                 "next_iteration", "_stop_next_iteration", "_task", 
                 "_sleeping", "_before_loop")
    def __init__(
        self, *, 
        loop: asyncio.AbstractEventLoop = ..., 
        coro = ...,
        times: Time | list[Time] | ListofTimeSequence  = ...,
    ) -> None:
        self.times = ListofTimeSequence(times, self)
        self.loop = loop or asyncio.new_event_loop()
        self.coro = coro
        self.current_iteration = 0
        self.next_iteration = 1
        self._stop_next_iteration = False
        self._task = None
        self._before_loop = asyncio.sleep(0)
        self._sleeping: asyncio.Future = False

    def _prepare_index(self):

        self.current_iteration = self.next_iteration

        if self.next_iteration == 0:
            self.times = ListofTimeSequence([t.to_next_week() for t in self.times if not t.once], self)

        if len(self.times) - 1 > self.current_iteration:
            self.next_iteration += 1
        else:
            self.next_iteration = 0
            
    async def _sleep(self):
        self._sleeping = self.loop.create_future()
        print("sleep for:",  self.times[self.current_iteration].to_seconds_from_now())
        self.loop.call_later(
            self.times[self.current_iteration].to_seconds_from_now(), 
            self._sleeping.set_result, 
            1
        )
        await self._sleeping
        
    async def _loop(self, *args, **kwargs):

        await self._before_loop()

        print(self.current_iteration, self.times[self.current_iteration], '|', self.next_iteration, self.times[self.next_iteration])

        if Time.now(self.times[self.current_iteration].tzinfo) < self.times[self.current_iteration]:
            print("sleeping now")
            await self._sleep()
        else:
            raise NotImplementedError("Time.now(self.times[self.current_iteration].tzinfo) > self.times[current_iteration]")
        print("done sleeping")

        while True:
            try:
                # yield true after future is _FINISHED
                # loop forever; every true value received,
                # do something
                await self.coro(*args, **kwargs)

            except asyncio.CancelledError:
                self.cancel()

            except Exception as err:
                await self.error(err)
                raise err

            else:
                if self._stop_next_iteration:
                    return
                
                self._prepare_index()

                print(self.current_iteration, self.times[self.current_iteration], '|', self.next_iteration, self.times[self.next_iteration])

                await self._sleep()
                print("after fut")

    def rewind_or_forward(self, index):
        self.next_iteration = index

    async def cancel(self):
        if not self._task.done():
            # store datas for restart, maybe
            info = {
                "current_iteration": self.current_iteration,
                "next_iteration": self.next_iteration,
                "stop_next_iteration": self._stop_next_iteration,
                "times": self.times,
                "coro": self.coro,
                "cancelled_at": Time.now()
            }
            self._task.cancel()
            print(info)
            # HACK db.push store
            return
        print("task is done")
        
    async def error(self, *args) -> None:
        exception: Exception = args[-1]
        print(
            f"Unhandled exception in internal background task {self.coro.__name__!r}.",
            file=sys.stderr,
        )
        traceback.print_exception(
            type(exception), exception, exception.__traceback__, file=sys.stderr
        )

    def start(self, *args, **kwargs) -> asyncio.Task:
        if self._task is not None and not self._task.done():
            raise RuntimeError("Task is already launched and is not completed.")
        print("start")
        self._task = self.loop.create_task(self._loop(*args, **kwargs))
        return self._task

    def before_loop(self, coro=None) -> Coroutine:
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError(f"Expected coroutine function, received {coro.__class__.__name__!r}.")
        self._before_loop = coro

async def foo():
    print("CALL AT >>", Time.now(Timezone(7)))

def print_time():
    print(Time.now(Timezone(7)))
    loop.call_later(5, print_time)


if __name__ == "__main__":

    loop = asyncio.new_event_loop()
    tm = [Time(2022, 11, 20, 21, 13, 50, tzinfo=Timezone(7)), 
         Time(2022, 11, 20, 21, 13, tzinfo=Timezone(7)), 
         Time(2022, 11, 20, 21, 13, 10, tzinfo=Timezone(7))]


    l = Loop(loop=loop, coro=foo, times=tm)
    l.before_loop(foo)
    print(l.times)

    task = l.start()
    loop.call_later(5, print_time)
    # loop.create_task(call())
    loop.run_forever()




