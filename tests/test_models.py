"""Tests for autoskope_client models."""

import pytest
from autoskope_client.models import Vehicle, VehiclePosition, _find_and_parse_position


class TestVehiclePosition:
    """Test VehiclePosition dataclass."""

    def test_vehicle_position_creation(self):
        """Test creating a VehiclePosition instance."""
        position = VehiclePosition(
            latitude=52.520008,
            longitude=13.404954,
            speed=50.0,
            timestamp="2025-01-23T12:00:00",
            park_mode=False,
        )

        assert position.latitude == 52.520008
        assert position.longitude == 13.404954
        assert position.speed == 50.0
        assert position.timestamp == "2025-01-23T12:00:00"
        assert position.park_mode is False


class TestFindAndParsePosition:
    """Test _find_and_parse_position function."""

    def test_parse_valid_position_data(self):
        """Test parsing valid GeoJSON position data."""
        position_data = {
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [13.404954, 52.520008]},
                    "properties": {
                        "s": "50.5",
                        "dt": "2025-01-23T12:00:00",
                        "park": 0,
                        "carid": "123",
                    },
                }
            ]
        }

        result = _find_and_parse_position(position_data)

        assert result is not None
        assert result.latitude == 52.520008
        assert result.longitude == 13.404954
        assert result.speed == 50.5
        assert result.timestamp == "2025-01-23T12:00:00"
        assert result.park_mode is False

    def test_parse_position_with_park_mode_true(self):
        """Test parsing position data with park mode enabled."""
        position_data = {
            "features": [
                {
                    "geometry": {"coordinates": [13.404954, 52.520008]},
                    "properties": {
                        "s": 0,
                        "dt": "2025-01-23T12:00:00",
                        "park": True,
                    },
                }
            ]
        }

        result = _find_and_parse_position(position_data)

        assert result is not None
        assert result.park_mode is True
        assert result.speed == 0.0

    def test_parse_empty_position_data(self):
        """Test parsing empty position data."""
        result = _find_and_parse_position(None)
        assert result is None

        result = _find_and_parse_position({})
        assert result is None

        result = _find_and_parse_position({"features": []})
        assert result is None

    def test_parse_malformed_position_data(self):
        """Test parsing malformed position data."""
        # Missing geometry
        position_data = {
            "features": [{"properties": {"s": 50, "dt": "2025-01-23T12:00:00"}}]
        }
        result = _find_and_parse_position(position_data)
        assert result is None

        # Missing properties
        position_data = {
            "features": [{"geometry": {"coordinates": [13.404954, 52.520008]}}]
        }
        result = _find_and_parse_position(position_data)
        assert result is None

        # Invalid coordinates
        position_data = {
            "features": [
                {
                    "geometry": {"coordinates": [13.404954]},  # Missing latitude
                    "properties": {"s": 50, "dt": "2025-01-23T12:00:00", "park": False},
                }
            ]
        }
        result = _find_and_parse_position(position_data)
        assert result is None


class TestVehicle:
    """Test Vehicle dataclass and factory methods."""

    def test_vehicle_from_api_minimal(self):
        """Test creating Vehicle from minimal API data."""
        api_data = {
            "id": "123",
            "name": "Test Vehicle",
            "ex_pow": "12.5",
            "bat_pow": "3.7",
            "hdop": "1.2",
        }

        vehicle = Vehicle.from_api(api_data)

        assert vehicle.id == "123"
        assert vehicle.name == "Test Vehicle"
        assert vehicle.external_voltage == 12.5
        assert vehicle.battery_voltage == 3.7
        assert vehicle.gps_quality == 1.2
        assert vehicle.position is None
        assert vehicle.imei is None

    def test_vehicle_from_api_with_position(self):
        """Test creating Vehicle with position data."""
        api_data = {
            "id": "123",
            "name": "Test Vehicle",
            "ex_pow": 12.5,
            "bat_pow": 3.7,
            "hdop": 1.2,
        }

        position_data = {
            "features": [
                {
                    "geometry": {"coordinates": [13.404954, 52.520008]},
                    "properties": {
                        "carid": "123",
                        "s": 50.0,
                        "dt": "2025-01-23T12:00:00",
                        "park": False,
                    },
                }
            ]
        }

        vehicle = Vehicle.from_api(api_data, position_data)

        assert vehicle.id == "123"
        assert vehicle.position is not None
        assert vehicle.position.latitude == 52.520008
        assert vehicle.position.longitude == 13.404954
        assert vehicle.position.speed == 50.0

    def test_vehicle_from_api_with_imei(self):
        """Test creating Vehicle with IMEI from support_infos."""
        api_data = {
            "id": "123",
            "name": "Test Vehicle",
            "ex_pow": 12.5,
            "bat_pow": 3.7,
            "hdop": 1.2,
            "support_infos": {"imei": "123456789012345"},
        }

        vehicle = Vehicle.from_api(api_data)

        assert vehicle.imei == "123456789012345"

    def test_vehicle_from_api_with_device_type(self):
        """Test creating Vehicle with device type mapping."""
        api_data = {
            "id": "123",
            "name": "Test Vehicle",
            "ex_pow": 12.5,
            "bat_pow": 3.7,
            "hdop": 1.2,
            "device_type_id": "1",  # Should map to a known model if DEVICE_TYPE_MODELS has it
        }

        vehicle = Vehicle.from_api(api_data)

        assert vehicle.model is not None  # Should have at least a default model

    def test_vehicle_from_api_invalid_data(self):
        """Test creating Vehicle with invalid data raises ValueError."""
        # Missing required fields
        api_data = {"id": "123"}

        with pytest.raises(ValueError, match="Invalid vehicle data structure"):
            Vehicle.from_api(api_data)

        # Invalid numeric values
        api_data = {
            "id": "123",
            "name": "Test",
            "ex_pow": "not_a_number",
            "bat_pow": 3.7,
            "hdop": 1.2,
        }

        with pytest.raises(ValueError, match="Invalid vehicle data structure"):
            Vehicle.from_api(api_data)

    def test_vehicle_from_api_position_mismatch(self):
        """Test that position is None when carid doesn't match."""
        api_data = {
            "id": "123",
            "name": "Test Vehicle",
            "ex_pow": 12.5,
            "bat_pow": 3.7,
            "hdop": 1.2,
        }

        position_data = {
            "features": [
                {
                    "geometry": {"coordinates": [13.404954, 52.520008]},
                    "properties": {
                        "carid": "999",  # Different car ID
                        "s": 50.0,
                        "dt": "2025-01-23T12:00:00",
                        "park": False,
                    },
                }
            ]
        }

        vehicle = Vehicle.from_api(api_data, position_data)

        assert vehicle.position is None  # Should not match different carid
