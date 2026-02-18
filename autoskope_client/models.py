"""Models for the Autoskope API."""

from dataclasses import dataclass
import logging
from typing import Any, TypedDict

from .constants import DEFAULT_MODEL, DEVICE_TYPE_MODELS

_LOGGER = logging.getLogger(__name__)


class GeoJsonProperties(TypedDict, total=False):
    """TypedDict for GeoJSON properties relevant to Autoskope."""

    s: str | float  # Speed
    dt: str  # Timestamp
    park: bool | int  # Park mode (can be 0/1 or boolean)
    carid: str | int  # Vehicle ID


class GeoJsonGeometry(TypedDict):
    """TypedDict for GeoJSON geometry."""

    type: str
    coordinates: list[float]


class GeoJsonFeature(TypedDict):
    """TypedDict for a GeoJSON feature."""

    type: str
    geometry: GeoJsonGeometry
    properties: GeoJsonProperties


class CannotConnect(Exception):
    """Exception raised when connection to the API fails."""


class InvalidAuth(Exception):
    """Exception raised for authentication errors."""


class VehicleInfoApi(TypedDict):
    """TypedDict for the 'info' part of the vehicle data from API."""

    id: str | int
    name: str
    ex_pow: str | float | int
    bat_pow: str | float | int
    hdop: str | float | int
    support_infos: dict[str, Any] | None
    device_type_id: str | int | None


class PositionDataApi(TypedDict, total=False):
    """TypedDict for the 'position_data' structure from API."""

    features: list[dict[str, Any]]


class AutoskopeError(Exception):
    """Base exception for Autoskope errors."""


@dataclass
class VehiclePosition:
    """Position information extracted from GeoJSON."""

    latitude: float
    longitude: float
    speed: float
    timestamp: str
    park_mode: bool


def _find_and_parse_position(
    position_data: PositionDataApi | None,
) -> VehiclePosition | None:
    """Parse GeoJSON data to extract vehicle position."""
    if not position_data or not position_data.get("features"):
        return None

    try:
        # Extract the first feature
        feature = position_data["features"][0]
        geometry = feature["geometry"]
        properties = feature["properties"]

        # Parse coordinates and properties
        longitude, latitude = geometry["coordinates"]
        speed = float(properties["s"])
        timestamp = properties["dt"]
        park_mode = bool(properties["park"])

        return VehiclePosition(
            latitude=latitude,
            longitude=longitude,
            speed=speed,
            timestamp=timestamp,
            park_mode=park_mode,
        )
    except (KeyError, ValueError, TypeError, IndexError) as e:
        _LOGGER.debug("Failed to parse position data: %s", e)
        return None


@dataclass
class Vehicle:
    """Class representing a vehicle."""

    id: str
    name: str
    position: Any | None
    external_voltage: float
    battery_voltage: float
    gps_quality: float  # Lower is better (HDOP)
    imei: str | None
    model: str

    @classmethod
    def from_api(
        cls,
        info: VehicleInfoApi,
        position_data: PositionDataApi | None = None,
    ) -> "Vehicle":
        """Create Vehicle object from API response dictionaries."""
        try:
            vehicle_id = str(info["id"])
            name = info["name"]
            # Convert numeric fields robustly
            ex_pow = float(info["ex_pow"])
            bat_pow = float(info["bat_pow"])
            hdop = float(info["hdop"])
        except (KeyError, ValueError, TypeError) as err:
            raise ValueError(f"Invalid vehicle data structure: {err}") from err

        # Find the matching position feature for this vehicle
        position = None
        if position_data and "features" in position_data:
            for feature in position_data["features"]:
                try:
                    carid = str(feature["properties"].get("carid"))
                    if carid == vehicle_id:
                        geometry = feature["geometry"]
                        properties = feature["properties"]
                        longitude, latitude = geometry["coordinates"]
                        speed = float(properties.get("s", 0))
                        timestamp = properties.get("dt", "")
                        park_mode = bool(properties.get("park", False))
                        position = VehiclePosition(
                            latitude=latitude,
                            longitude=longitude,
                            speed=speed,
                            timestamp=timestamp,
                            park_mode=park_mode,
                        )
                        break
                except (KeyError, TypeError, ValueError) as e:
                    _LOGGER.debug("Exception while matching carid: %s", e)
                    continue

        # Use .get() for optional fields/dicts
        support_infos = info.get("support_infos")
        imei = support_infos.get("imei") if isinstance(support_infos, dict) else None
        device_type = str(info.get("device_type_id", ""))
        model = DEVICE_TYPE_MODELS.get(device_type, DEFAULT_MODEL)

        return cls(
            id=vehicle_id,
            name=name,
            position=position,
            external_voltage=ex_pow,
            battery_voltage=bat_pow,
            gps_quality=hdop,
            imei=imei,
            model=model,
        )
