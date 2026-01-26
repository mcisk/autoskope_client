"""Integration tests for autoskope_client with real API calls.

These tests require valid credentials set as environment variables:
- AUTOSKOPE_HOST
- AUTOSKOPE_USERNAME
- AUTOSKOPE_PASSWORD

Run with:
    pytest tests/test_integration.py -v

Or skip integration tests:
    pytest -v -m "not integration"
"""

import os
import pytest

from autoskope_client import AutoskopeApi, InvalidAuth, CannotConnect


# Check if credentials are available
CREDENTIALS_AVAILABLE = all([
    os.getenv("AUTOSKOPE_HOST"),
    os.getenv("AUTOSKOPE_USERNAME"),
    os.getenv("AUTOSKOPE_PASSWORD"),
])

skip_if_no_credentials = pytest.mark.skipif(
    not CREDENTIALS_AVAILABLE,
    reason="Integration tests require AUTOSKOPE_HOST, AUTOSKOPE_USERNAME, and AUTOSKOPE_PASSWORD environment variables"
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestRealApiIntegration:
    """Integration tests with real API calls."""

    @skip_if_no_credentials
    async def test_authentication_with_valid_credentials(self):
        """Test authentication with real credentials."""
        api = AutoskopeApi(
            host=os.getenv("AUTOSKOPE_HOST"),
            username=os.getenv("AUTOSKOPE_USERNAME"),
            password=os.getenv("AUTOSKOPE_PASSWORD"),
        )

        try:
            await api.connect()
            assert api.is_connected is True
            assert api._authenticated is True
        finally:
            await api.close()

    @skip_if_no_credentials
    async def test_context_manager_with_real_api(self):
        """Test context manager usage with real API."""
        async with AutoskopeApi(
            host=os.getenv("AUTOSKOPE_HOST"),
            username=os.getenv("AUTOSKOPE_USERNAME"),
            password=os.getenv("AUTOSKOPE_PASSWORD"),
        ) as api:
            assert api.is_connected is True

    @skip_if_no_credentials
    async def test_get_vehicles_returns_data(self):
        """Test fetching real vehicle data from API."""
        async with AutoskopeApi(
            host=os.getenv("AUTOSKOPE_HOST"),
            username=os.getenv("AUTOSKOPE_USERNAME"),
            password=os.getenv("AUTOSKOPE_PASSWORD"),
        ) as api:
            vehicles = await api.get_vehicles()

            # Should return a list (may be empty if no vehicles)
            assert isinstance(vehicles, list)

            # If vehicles exist, validate structure
            if vehicles:
                print(f"\n✓ Found {len(vehicles)} vehicle(s)")
                print("=" * 70)

                for idx, vehicle in enumerate(vehicles, 1):
                    # Validate structure for each vehicle
                    assert hasattr(vehicle, "id")
                    assert hasattr(vehicle, "name")
                    assert hasattr(vehicle, "position")
                    assert hasattr(vehicle, "external_voltage")
                    assert hasattr(vehicle, "battery_voltage")
                    assert hasattr(vehicle, "gps_quality")
                    assert hasattr(vehicle, "imei")
                    assert hasattr(vehicle, "model")

                    # Validate types
                    assert isinstance(vehicle.id, str)
                    assert isinstance(vehicle.name, str)
                    assert isinstance(vehicle.external_voltage, float)
                    assert isinstance(vehicle.battery_voltage, float)
                    assert isinstance(vehicle.gps_quality, float)

                    # Position might be None
                    if vehicle.position:
                        assert hasattr(vehicle.position, "latitude")
                        assert hasattr(vehicle.position, "longitude")
                        assert hasattr(vehicle.position, "speed")
                        assert hasattr(vehicle.position, "timestamp")
                        assert hasattr(vehicle.position, "park_mode")

                    # Print detailed info for each vehicle
                    print(f"\nVehicle #{idx}: {vehicle.name}")
                    print(f"  ID: {vehicle.id}")
                    print(f"  Model: {vehicle.model}")
                    print(f"  External Voltage: {vehicle.external_voltage}V")
                    print(f"  Battery Voltage: {vehicle.battery_voltage}V")
                    print(f"  GPS Quality (HDOP): {vehicle.gps_quality}")
                    print(f"  IMEI: {vehicle.imei or 'N/A'}")

                    if vehicle.position:
                        print(f"  Position:")
                        print(f"    Latitude: {vehicle.position.latitude}")
                        print(f"    Longitude: {vehicle.position.longitude}")
                        print(f"    Speed: {vehicle.position.speed} km/h")
                        print(f"    Timestamp: {vehicle.position.timestamp}")
                        print(f"    Parked: {'Yes' if vehicle.position.park_mode else 'No'}")
                    else:
                        print(f"  Position: No position data available")

                print("=" * 70)

    @skip_if_no_credentials
    async def test_authentication_failure_with_wrong_password(self):
        """Test that wrong password raises InvalidAuth."""
        api = AutoskopeApi(
            host=os.getenv("AUTOSKOPE_HOST"),
            username=os.getenv("AUTOSKOPE_USERNAME"),
            password="wrong_password_12345",
        )

        with pytest.raises(InvalidAuth):
            await api.connect()

        await api.close()

    @skip_if_no_credentials
    async def test_custom_timeout_works(self):
        """Test that custom timeout parameter works."""
        async with AutoskopeApi(
            host=os.getenv("AUTOSKOPE_HOST"),
            username=os.getenv("AUTOSKOPE_USERNAME"),
            password=os.getenv("AUTOSKOPE_PASSWORD"),
            timeout=30,
        ) as api:
            vehicles = await api.get_vehicles()
            assert isinstance(vehicles, list)

    @pytest.mark.asyncio
    async def test_invalid_host_raises_error(self):
        """Test that invalid host raises CannotConnect."""
        api = AutoskopeApi(
            host="https://invalid-host-that-does-not-exist-12345.com",
            username="test",
            password="test",
        )

        with pytest.raises(CannotConnect):
            await api.connect()

        await api.close()
