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

### Using Custom Timeout

```python
import asyncio
from autoskope_client import AutoskopeApi

async def main():
    # Set custom timeout (default is 20 seconds)
    async with AutoskopeApi(
        host="https://portal.autoskope.de",
        username="your_username",
        password="your_password",
        timeout=30  # Custom timeout in seconds
    ) as api:
        vehicles = await api.get_vehicles()
        print(f"Found {len(vehicles)} vehicles")

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
- `park_mode`: Whether vehicle is parked

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

## Development

### Running Tests

Install test dependencies:

```bash
pip install -e ".[test]"
```

Run unit tests only (no API calls):

```bash
pytest -v -m "not integration"
```

Run all tests including integration tests (requires credentials):

```bash
# Set environment variables first
export AUTOSKOPE_HOST=https://portal.autoskope.de
export AUTOSKOPE_USERNAME=your_username
export AUTOSKOPE_PASSWORD=your_password

# Run all tests
pytest -v
```

Run tests with coverage:

```bash
pytest --cov=autoskope_client --cov-report=html
```

### Integration Tests

Integration tests make real API calls and require valid credentials. They are marked with `@pytest.mark.integration` and will be skipped automatically if credentials are not set.

**Secure way to run integration tests** (recommended):

```bash
# Option 1: Using the secure test runner (password hidden)
python run_integration_tests.py

# Option 2: Using .env file
cp .env.example .env
# Edit .env with your credentials
pip install python-dotenv
python run_integration_tests.py
```

To run only integration tests:

```bash
pytest -v -m integration
```

**Security Note:** Never commit credentials to git. The `.env` file is excluded via `.gitignore`.

## Author

Nico Liebeskind (nico@autoskope.de)