"""Autoskope API Client."""

import json
import logging
from typing import Any

import aiohttp

from .constants import APP_VERSION
from .models import CannotConnect, InvalidAuth, Vehicle

_LOGGER = logging.getLogger(__name__)


class AutoskopeApi:
    """Client to interact with the Autoskope API."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        session: aiohttp.ClientSession | None = None,
        timeout: int = 20,
    ) -> None:
        """Initialize the Autoskope API client.

        Args:
            host: API host URL
            username: Account username
            password: Account password
            session: Optional external session (for non-cookie scenarios)
            timeout: Request timeout in seconds (default: 20)

        Raises:
            ValueError: If host is not a valid HTTP(S) URL
        """
        # Validate host URL
        if not host.startswith(("http://", "https://")):
            raise ValueError(
                f"Host must be a valid HTTP(S) URL, got: {host}"
            )

        self._host = host.rstrip("/")
        self._username = username
        self._password = password
        self._timeout = timeout
        self._authenticated = False
        self._form_headers = {"Content-Type": "application/x-www-form-urlencoded"}
        self._json_headers = {"Content-Type": "application/json"}

        if session:
            self._session = session
            self._owns_session = False
            self._cookie_jar = None
        else:
            self._session = None
            self._owns_session = True
            self._cookie_jar = None

    async def __aenter__(self) -> "AutoskopeApi":
        """Context manager entry - connect and authenticate."""
        try:
            await self.connect()
            return self
        except Exception:
            # Ensure cleanup if connect fails
            await self.close()
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - cleanup session."""
        await self.close()

    async def connect(self) -> None:
        """Create session (if needed) and authenticate."""
        if self._owns_session and not self._session:
            # Create cookie jar lazily when session is created
            if self._cookie_jar is None:
                self._cookie_jar = aiohttp.CookieJar()
            self._session = aiohttp.ClientSession(
                cookie_jar=self._cookie_jar,
                headers={"User-Agent": f"autoskope-client/{APP_VERSION}"},
            )

        if not self._authenticated:
            await self.authenticate()

    async def close(self) -> None:
        """Close session if owned by this instance."""
        if self._session and self._owns_session:
            await self._session.close()
            self._session = None
        self._authenticated = False

    @property
    def is_connected(self) -> bool:
        """Check if API is connected and authenticated."""
        return self._session is not None and self._authenticated

    async def _request(
        self,
        method: str,
        path: str,
        data: dict[str, Any] | None = None,
        json_payload: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make an API request and handle responses."""
        if not self._session:
            raise RuntimeError("Not connected. Call connect() first or use context manager.")

        url = f"{self._host}{path}"
        headers = self._form_headers

        _LOGGER.debug("Requesting %s %s", method.upper(), url)

        response_text: str | None = None
        response_json: dict[str, Any] | None = None
        error_to_raise: Exception | None = None

        try:
            async with self._session.request(
                method,
                url,
                headers=headers,
                data=data,
                **kwargs,
            ) as response:
                response_status = response.status
                _LOGGER.debug("Response status for %s: %s", url, response_status)

                response_text = await response.text()

                if response_status == 202:
                    _LOGGER.debug(
                        "Login response body (status 202): %s", response_text[:200]
                    )
                    try:
                        response_json_202 = json.loads(response_text)
                        if isinstance(response_json_202, dict) and (
                            message := response_json_202.get("message")
                        ):
                            if isinstance(message, str) and message.startswith(
                                "Du verwendest eine veraltete App-Version"
                            ):
                                _LOGGER.debug(
                                    "API reports outdated client version, but proceeding: %s",
                                    message,
                                )
                    except json.JSONDecodeError:
                        _LOGGER.debug(
                            "Received non-JSON response on status 202, proceeding anyway"
                        )
                    return {}

                if path == "/scripts/ajax/login.php":
                    _LOGGER.debug(
                        "Login response body (status %s): %s",
                        response_status,
                        response_text[:200],
                    )
                    if response_status == 200 and not response_text.strip():
                        return {}
                    error_to_raise = InvalidAuth(
                        "Authentication failed (non-200 status or non-empty body)"
                    )
                elif response_status in (401, 403):
                    error_to_raise = InvalidAuth(
                        f"Authorization error: {response_status}"
                    )
                elif response_status >= 400:
                    error_to_raise = CannotConnect(
                        f"API request failed with status {response_status}"
                    )
                else:
                    try:
                        response_json = json.loads(response_text)
                        if not isinstance(response_json, dict):
                            _LOGGER.warning("API response is not a JSON dictionary")
                            error_to_raise = CannotConnect(
                                "Received non-dictionary JSON response from API"
                            )
                    except json.JSONDecodeError as json_err:
                        _LOGGER.error("Failed to decode API response: %s", json_err)
                        error_to_raise = CannotConnect(
                            "Received invalid response from API"
                        )
                        error_to_raise.__cause__ = json_err

        except aiohttp.ClientError as err:
            _LOGGER.error("API request connection error for %s: %s", url, err)
            raise CannotConnect(f"Error connecting to Autoskope API: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error during API request to %s", url)
            raise CannotConnect(f"Unexpected API error: {err}") from err

        if error_to_raise:
            raise error_to_raise

        return response_json if response_json is not None else {}

    async def authenticate(self) -> bool:
        """Authenticate with the API and verify success."""
        if not self._session:
            raise RuntimeError("Not connected. Call connect() first.")

        try:
            await self._request(
                "post",
                "/scripts/ajax/login.php",
                data={
                    "username": self._username,
                    "password": self._password,
                    "appversion": APP_VERSION,
                },
                timeout=self._timeout,
            )
        except InvalidAuth as err:
            _LOGGER.warning("Authentication failed for user %s", self._username)
            self._authenticated = False
            raise InvalidAuth("Authentication failed") from err
        except CannotConnect as err:
            _LOGGER.error(
                "Connection error during authentication for user %s", self._username
            )
            self._authenticated = False
            raise CannotConnect("Connection error during authentication") from err
        except Exception as err:
            _LOGGER.exception(
                "Unexpected error during authentication for user %s", self._username
            )
            self._authenticated = False
            raise CannotConnect(
                f"Unexpected error during authentication: {err}"
            ) from err
        else:
            _LOGGER.debug("Authentication successful for user %s", self._username)
            self._authenticated = True
            return True

    async def get_vehicles(self) -> list[Vehicle]:
        """Fetch and parse vehicles data from the API."""
        if not self._session:
            raise RuntimeError("Not connected. Call connect() first.")

        _LOGGER.debug("Attempting to fetch vehicle data")
        vehicles: list[Vehicle] = []
        error_to_raise: Exception | None = None

        try:
            data = await self._request(
                "post",
                "/scripts/ajax/app/info.php",
                data={"appversion": APP_VERSION},
                timeout=self._timeout,
            )

            last_pos_str = data.get("lastPos")
            carid_to_feature = {}
            if isinstance(last_pos_str, str) and last_pos_str:
                try:
                    pos_geojson = json.loads(last_pos_str)
                    if (
                        isinstance(pos_geojson, dict)
                        and pos_geojson.get("type") == "FeatureCollection"
                        and isinstance(pos_geojson.get("features"), list)
                    ):
                        for feature in pos_geojson["features"]:
                            if (
                                isinstance(feature, dict)
                                and isinstance(feature.get("properties"), dict)
                                and "carid" in feature["properties"]
                            ):
                                carid = str(feature["properties"]["carid"])
                                carid_to_feature[carid] = feature
                        _LOGGER.debug(
                            "Built carid_to_feature map with %d entries",
                            len(carid_to_feature),
                        )
                    else:
                        _LOGGER.debug(
                            "Parsed lastPos data is not a valid FeatureCollection"
                        )
                except json.JSONDecodeError:
                    _LOGGER.debug("Failed to parse lastPos JSON string")
            elif last_pos_str is not None:
                _LOGGER.debug(
                    "The lastPos data is not a string: %s", type(last_pos_str)
                )

            cars_list = data.get("cars", [])
            _LOGGER.debug(
                "Received cars list with %d vehicles",
                len(cars_list) if isinstance(cars_list, list) else 0,
            )
            if not isinstance(cars_list, list):
                _LOGGER.error("Vehicle data 'cars' is not a list")
                error_to_raise = CannotConnect(
                    "Invalid vehicle data format in API response"
                )
            else:
                for car_info in cars_list:
                    if not isinstance(car_info, dict):
                        _LOGGER.warning("Skipping non-dictionary item in cars list")
                        continue
                    try:
                        car_id = str(car_info.get("id"))
                        vehicle_position_data = carid_to_feature.get(car_id)
                        if vehicle_position_data:
                            position_data = {"features": [vehicle_position_data]}
                        else:
                            position_data = None
                        vehicles.append(
                            Vehicle.from_api(
                                car_info,
                                position_data,
                            )
                        )
                    except ValueError as e:
                        vehicle_id = car_info.get("id", "unknown")
                        _LOGGER.warning(
                            "Failed to parse vehicle data for ID %s: %s",
                            vehicle_id,
                            e,
                        )

        except InvalidAuth as err:
            _LOGGER.error("Authentication error during vehicle fetch")
            self._authenticated = False
            raise InvalidAuth("Authentication required") from err
        except CannotConnect as err:
            _LOGGER.error(
                "Failed to fetch vehicle data due to connection/API error: %s", err
            )
            raise CannotConnect(
                f"Failed to fetch data from Autoskope API: {err}"
            ) from err
        except Exception as err:
            _LOGGER.exception("Unexpected error processing vehicle data")
            raise CannotConnect(
                f"Unexpected error processing vehicle data: {err}"
            ) from err

        if error_to_raise:
            raise error_to_raise

        _LOGGER.debug("Successfully parsed %d vehicles", len(vehicles))
        return vehicles