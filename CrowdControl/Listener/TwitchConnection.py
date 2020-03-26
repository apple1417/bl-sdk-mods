import asyncio
import json
import logging
import random
import requests
import sys
import websockets
from typing import Any, ClassVar, List, TextIO, Union

_log = logging.getLogger("CrowdControlListener.Connection")


class TwitchError(Exception):
    fatal: bool

    def __init__(self, msg: str, detail: Any = None, *, fatal: bool = False) -> None:
        super().__init__(msg)

        level = logging.CRITICAL if fatal else logging.ERROR
        _log.log(level, msg)
        if detail is not None:
            _log.log(logging.DEBUG + 1, str(detail))
        self.fatal = fatal


class TwitchReconnect(Exception):
    pass


class TwitchConnection:
    ping_interval: ClassVar[float] = 150
    ping_range: ClassVar[float] = 5
    output: ClassVar[TextIO] = sys.stdout

    oauth_token: str

    has_connected: bool
    has_closed: bool

    tasks: List[asyncio.Future]  # type: ignore

    _user_id: str
    _socket: websockets.WebSocketClientProtocol
    _ping_task: asyncio.Future  # type: ignore
    _recv_task: asyncio.Future  # type: ignore
    _recent_pong: bool

    def __init__(self, token: str) -> None:
        _log.info("Creating new twitch connection")

        self.oauth_token = token

        self.has_connected = False
        self.has_closed = False

        self.tasks = []

    def validate_token(self) -> None:
        resp = requests.get(
            "https://id.twitch.tv/oauth2/validate",
            headers={
                "Authorization": f"OAuth {self.oauth_token}"
            }
        )
        try:
            # I know requests has a built in for this but I like the more specific exception
            resp_dict = json.loads(resp.text)
            if "status" in resp_dict and resp_dict["status"] == 401:
                raise TwitchError("Invalid OAuth Token", fatal=True)
            if "channel:read:redemptions" not in resp_dict["scopes"]:
                raise TwitchError(
                    "OAuth token does not have neccessary privilages!",
                    resp_dict["scopes"],
                    fatal=True
                )
            self._user_id = resp_dict["user_id"]
        except (json.JSONDecodeError, KeyError):
            raise TwitchError("Could not parse validation response", resp.text)

    async def connect(self) -> None:
        self.validate_token()

        self._socket = await websockets.connect("wss://pubsub-edge.twitch.tv")
        await self._socket.send(json.dumps({"type": "PING"}))

        resp = await self._socket.recv()
        self._validate_pong(resp)

        await self._socket.send(json.dumps({
            "type": "LISTEN",
            "data": {
                "topics": [
                    "channel-points-channel-v1." + self._user_id
                ],
                "auth_token": self.oauth_token
            }
        }))

        resp = await self._socket.recv()
        try:
            resp_dict = json.loads(resp)
            if resp_dict["type"] == "RECONNECT":
                raise TwitchReconnect()
            elif resp_dict["type"] != "RESPONSE":
                raise TwitchError("Did not recieve valid connection response from Twitch", resp)
        except (json.JSONDecodeError, KeyError):
            raise TwitchError("Could not parse Twitch connection response", resp)

        self.has_connected = True
        self._ping_task = asyncio.create_task(self._keep_alive())
        self._recv_task = asyncio.create_task(self._handle_messages())
        self.tasks.append(self._ping_task)
        self.tasks.append(self._recv_task)

    async def close(self) -> None:
        if not self.has_connected or self.has_closed:
            return

        self.has_closed = True
        for task in (self._ping_task, self._recv_task):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        await self._socket.close()

    def _validate_pong(self, resp: Union[str, bytes]) -> None:
        try:
            resp_dict = json.loads(resp)
            if resp_dict["type"] == "RECONNECT":
                raise TwitchReconnect()
            elif resp_dict["type"] != "PONG":
                raise TwitchError("Did not recieve 'PONG' from Twitch", resp)
        except (json.JSONDecodeError, KeyError):
            raise TwitchError("Could not parse Twitch pong response", resp)
        self._recent_pong = True

    async def _keep_alive(self) -> None:
        while True:
            time = random.uniform(
                self.ping_interval - self.ping_range,
                self.ping_interval + self.ping_range
            )
            await asyncio.sleep(time)

            self._recent_pong = False
            await self._socket.send(json.dumps({"type": "PING"}))

            await asyncio.sleep(11)
            if not self._recent_pong:
                raise TwitchReconnect()

    async def _handle_messages(self) -> None:
        while True:
            resp = await self._socket.recv()
            try:
                resp_dict = json.loads(resp)
                if resp_dict["type"] == "RECONNECT":
                    raise TwitchReconnect()
                elif resp_dict["type"] == "PONG":
                    self._validate_pong(resp)
                elif resp_dict["type"] != "MESSAGE":
                    raise TwitchError("Did not recieve valid response type from Twitch", resp)
                else:
                    self.output.write(resp_dict["data"]["message"].replace("\n", "\\n") + "\n")
                    self.output.flush()
            except (json.JSONDecodeError, KeyError):
                raise TwitchError("Could not parse Twitch message", resp)
