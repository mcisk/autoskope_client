# Autoskope Client

A Python client library for interacting with the Autoskope vehicle tracking API.

## Features

- Async/await support using aiohttp
- Session management with cookie isolation
- Context manager support for automatic cleanup
- Type hints for better IDE support
- Comprehensive error handling

## Installation

```bash
pip install autoskope-client
```

## Usage

### Basic Usage with Context Manager

```python
import asyncio
from autoskope_client import AutoskopeApi

async def main():
    async with AutoskopeApi(
        host="https://portal.autoskope.de",
        username="your_username",
        password="your_password"
    ) as api:
        # Get all vehicles
        vehicles = await api.get_vehicles()

        for vehicle in vehicles:
            print(f"Vehicle: {vehicle.name}")
            if vehicle.position:
                print(f"  Location: {vehicle.position.latitude}, {vehicle.position.longitude}")
                print(f"  Speed: {vehicle.position.speed} km/h")

asyncio.run(main())
```

### Manual Session Management

```python
import asyncio
from autoskope_client import AutoskopeApi

async def main():
    api = AutoskopeApi(
        host="https://portal.autoskope.de",
        username="your_username",
        password="your_password"
    )

    try:
        await api.connect()
        vehicles = await api.get_vehicles()

        for vehicle in vehicles:
            print(f"Vehicle: {vehicle.name}")
    finally:
        await api.close()

asyncio.run(main())
```

### Using with External Session

```python
import asyncio
import aiohttp
from autoskope_client import AutoskopeApi

async def main():
    async with aiohttp.ClientSession() as session:
        api = AutoskopeApi(
            host="https://portal.autoskope.de",
            username="your_username",
            password="your_password",
            session=session  # Use external session
        )

        await api.connect()
        vehicles = await api.get_vehicles()

asyncio.run(main())
```

## Data Models

### Vehicle
- `id`: Unique identifier
- `name`: Vehicle name
- `model`: Vehicle model
- `battery_voltage`: Battery voltage in volts
- `external_voltage`: External power voltage in volts
- `gps_quality`: GPS quality (HDOP - lower is better)
- `imei`: Device IMEI
- `position`: Current position (if available)

### VehiclePosition
- `latitude`: Latitude coordinate
- `longitude`: Longitude coordinate
- `speed`: Speed in km/h
- `timestamp`: Position timestamp
- `is_parked`: Whether vehicle is parked

## Error Handling

The library defines two main exception types:

- `InvalidAuth`: Raised when authentication fails
- `CannotConnect`: Raised when connection to the API fails

```python
from autoskope_client import AutoskopeApi, InvalidAuth, CannotConnect

try:
    async with AutoskopeApi(...) as api:
        vehicles = await api.get_vehicles()
except InvalidAuth:
    print("Authentication failed. Check credentials.")
except CannotConnect:
    print("Could not connect to Autoskope API.")
```

## Requirements

- Python 3.8+
- aiohttp >= 3.8.0

## Author

Nico Liebeskind (nico@autoskope.de)