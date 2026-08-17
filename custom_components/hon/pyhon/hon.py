import asyncio
import logging
from pathlib import Path
from types import TracebackType
from typing import List, Optional, Dict, Any, Type, Callable

from aiohttp import ClientSession
from typing_extensions import Self

from .appliance import HonAppliance
from .connection.api import HonAPI
from .connection.api import TestAPI
from .connection.mqtt import MQTTClient
from .exceptions import ApiError, HonConnectionError, NoAuthenticationException

_LOGGER = logging.getLogger(__name__)


# pylint: disable=too-many-instance-attributes
class Hon:
    def __init__(
        self,
        email: Optional[str] = "",
        password: Optional[str] = "",
        session: Optional[ClientSession] = None,
        mobile_id: str = "",
        refresh_token: str = "",
        test_data_path: Optional[Path] = None,
    ):
        self._email: Optional[str] = email
        self._password: Optional[str] = password
        self._session: ClientSession | None = session
        self._appliances: List[HonAppliance] = []
        self._api: Optional[HonAPI] = None
        self._test_data_path: Path = test_data_path or Path().cwd()
        self._mobile_id: str = mobile_id
        self._refresh_token: str = refresh_token
        self._mqtt_client: MQTTClient | None = None
        self._notify_function: Optional[Callable[[Any], None]] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    async def __aenter__(self) -> Self:
        return await self.create()

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await self.close()

    @property
    def api(self) -> HonAPI:
        if self._api is None:
            raise NoAuthenticationException
        return self._api

    @property
    def email(self) -> str:
        if not self._email:
            raise ValueError("Missing email")
        return self._email

    @property
    def password(self) -> str:
        if not self._password:
            raise ValueError("Missing password")
        return self._password

    async def create(self) -> Self:
        self._loop = asyncio.get_running_loop()
        self._api = await HonAPI(
            self.email,
            self.password,
            session=self._session,
            mobile_id=self._mobile_id,
            refresh_token=self._refresh_token,
        ).create()
        await self.setup()
        return self

    @property
    def appliances(self) -> List[HonAppliance]:
        return self._appliances

    @appliances.setter
    def appliances(self, appliances: List[HonAppliance]) -> None:
        self._appliances = appliances

    async def _create_appliance(
        self, appliance_data: Dict[str, Any], api: HonAPI, zone: int = 0
    ) -> None:
        appliance = HonAppliance(api, appliance_data, zone=zone)
        if appliance.mac_address == "":
            return
        try:
            await appliance.load_commands()
            await appliance.load_attributes()
            await appliance.load_statistics()
            self._appliances.append(appliance)
        except (
            KeyError,
            ValueError,
            IndexError,
            HonConnectionError,
            ApiError,
        ) as error:
            _LOGGER.exception(error)
            _LOGGER.error("Device data - %s", appliance_data)

    async def setup(self) -> None:
        appliances = await self.api.load_appliances()
        for appliance in appliances:
            if (zones := int(appliance.get("zone", "0"))) > 1:
                for zone in range(zones):
                    await self._create_appliance(
                        appliance.copy(), self.api, zone=zone + 1
                    )
            await self._create_appliance(appliance, self.api)
        if (
            self._test_data_path
            and (
                test_data := self._test_data_path / "hon-test-data" / "test_data"
            ).exists()
            or (test_data := test_data / "..").exists()
        ):
            api = TestAPI(test_data)
            for appliance in await api.load_appliances():
                await self._create_appliance(appliance, api)
        if not self._mqtt_client:
            self._mqtt_client = await MQTTClient(self, self._mobile_id).create()

    def subscribe_updates(self, notify_function: Callable[[Any], None]) -> None:
        self._notify_function = notify_function

    def notify(self) -> None:
        # May be called from the MQTT client's native callback thread, not
        # the event loop thread - marshal it back so consumers (e.g. HA's
        # DataUpdateCoordinator) don't touch loop-bound state off-thread.
        if self._notify_function is None:
            return
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._notify_function, None)
        else:
            self._notify_function(None)

    async def close(self) -> None:
        if self._mqtt_client is not None:
            await self._mqtt_client.close()
            self._mqtt_client = None
        await self.api.close()
