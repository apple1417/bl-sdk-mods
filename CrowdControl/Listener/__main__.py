import argparse
import asyncio
import atexit
import logging
import random
import sys
import traceback

from datetime import datetime
from logging.handlers import RotatingFileHandler
from os import path
from socket import gaierror
from requests.exceptions import ConnectionError
from typing import ClassVar, List, Optional

from .TwitchConnection import TwitchConnection, TwitchError, TwitchReconnect


handler = RotatingFileHandler(path.join(path.dirname(__file__), "listener.log"), "a", 1000000, 2)
logging.basicConfig(
    format="%(asctime)s %(levelname)s: %(name)s - %(message)s",
    handlers=[handler],
    level=logging.INFO
)
_log = logging.getLogger("CrowdControlListener")
_log.info("Starting up")


class Program:
    reconnect_times: ClassVar[List[float]] = [
        0, 1, 2, 5, 10, 15, 30, 60
    ]
    reconnect_range: ClassVar[float] = 1
    reconnect_reset: ClassVar[float] = 120
    _reconnect_stage: int
    _last_reconnect: Optional[datetime]

    token: str

    _conn: TwitchConnection
    _loop: asyncio.AbstractEventLoop

    max_duplicate_errors: ClassVar[int] = 3
    _last_error: Optional[Exception]
    _error_count: int

    def __init__(self, token: str) -> None:
        self.token = token
        self._loop = asyncio.get_event_loop()

        self._reconnect_stage = 0
        self._error_count = 0
        self._last_reconnect = None
        self._last_error = None

    def _print_msg(self, msg: str) -> None:
        msg = msg.replace("\n", "\\n")
        _log.error(msg)
        sys.stderr.write(f"MSG: {msg}\n")
        sys.stderr.flush()

    def _print_fatal(self, msg: str) -> None:
        msg = msg.replace("\n", "\\n")
        _log.critical(msg)
        sys.stderr.write(f"FTL: {msg}\n")
        sys.stderr.flush()

    def run(self) -> None:
        self._loop.run_until_complete(self._run())
        self.close()

    async def _run(self) -> None:
        while True:
            self._conn = TwitchConnection(self.token)
            try:
                await self._conn.connect()
            except (ConnectionError, gaierror, TwitchError, TwitchReconnect) as ex:
                if await self._handle_exception(ex):
                    return
                continue

            if self._last_reconnect is not None:
                self._print_msg("Reconnected.")
            self._last_reconnect = datetime.now()

            done, pend = await asyncio.wait(self._conn.tasks, return_when=asyncio.FIRST_EXCEPTION)

            for task in done:
                ex2 = task.exception()
                if ex2 is None:
                    continue
                if await self._handle_exception(ex2):
                    return

    async def _handle_exception(self, ex: BaseException) -> bool:
        # If enough time has passed between the last error and this, reset the counters
        if self._last_reconnect is not None:
            if (datetime.now() - self._last_reconnect).seconds > self.reconnect_reset:
                self._reconnect_stage = 0
                self._error_count = 0

        if self._reconnect_stage == len(self.reconnect_times):
            self._print_fatal("Unable to reconnect to Twitch!")
            return True
        time = max(0, random.uniform(
            self.reconnect_times[self._reconnect_stage] - self.reconnect_range,
            self.reconnect_times[self._reconnect_stage] + self.reconnect_range
        ))
        reconnect_str = f"in {self.reconnect_times[self._reconnect_stage]} seconds."
        if self._reconnect_stage == 0:
            time = 0
            reconnect_str = "now."
        self._reconnect_stage += 1

        try:
            # This should re-throw the same exception we've analysing
            # Not grabbing the traceback here though just in case
            await self._conn.close()
        except Exception:
            pass

        tb: str
        try:
            raise ex
        except Exception:
            tb = traceback.format_exc()

        if isinstance(ex, TwitchError):
            if ex.fatal:
                self._print_fatal(str(ex))
                return True
            if str(self._last_error) == str(ex):
                self._error_count += 1
            else:
                self._error_count = 0
            if self._error_count >= self.max_duplicate_errors:
                self._print_fatal("Could not recover from internal errors!")
                return True
            else:
                self._print_msg(f"Internal error, reconnecting {reconnect_str}")
        elif isinstance(ex, TwitchReconnect) or isinstance(ex, ConnectionError) or isinstance(ex, gaierror):
            self._print_msg(f"Lost connection, reconnecting {reconnect_str}")
        else:
            self._print_fatal(f"Unexpected Exception!\n{ex}\n{tb}")
            return True

        self._last_error = ex
        await asyncio.sleep(time)
        return False

    def close(self) -> None:
        _log.info("Shutting down")
        self._loop.run_until_complete(self._close())

    async def _close(self) -> None:
        await self._conn.close()
        self._loop.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Listener")
    parser.add_argument("token", action="store")
    args = parser.parse_args()

    prog = Program(args.token)
    atexit.register(prog.close)
    prog.run()
