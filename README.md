# autoskope_client

Python client library for the Autoskope API.

## Installation

```bash
pip install autoskope-client
```

## Usage

```python
import asyncio
from autoskope_client import AutoskopeApi

async def main():
    # Initialize the client
    api = AutoskopeApi(
        host="https://your-autoskope-host.com", 
        username="your_username", 
        password="your_password"
    )
    
    # Authenticate with the API
    try:
        await api.authenticate()
        print("Authentication successful")
        
        # Get vehicles
        vehicles = await api.get_vehicles()
        for vehicle in vehicles:
            print(f"Vehicle: {vehicle.name}")
            print(f"Position: {vehicle.position.latitude}, {vehicle.position.longitude}")
            print(f"Speed: {vehicle.position.speed} km/h")
            print(f"Park mode: {'Yes' if vehicle.position.park_mode else 'No'}")
            print("---")
            
    except Exception as err:
        print(f"Error: {err}")

# Run the example
if __name__ == "__main__":
    asyncio.run(main())
```

## Features

- Authentication with the Autoskope API
- Retrieve vehicle information
- Get real-time vehicle position data

## License

MIT License