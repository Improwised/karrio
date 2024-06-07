
# karrio.ninja_van

This package is a Ninja Van extension of the [karrio](https://pypi.org/project/karrio) multi carrier shipping SDK.

## Requirements

`Python 3.7+`

## Installation

```bash
pip install karrio.ninja_van
```

## Usage

```python
import karrio
from karrio.mappers.ninja_van.settings import Settings


# Initialize a carrier gateway
ninja_van = karrio.gateway["ninja_van"].create(
    Settings(
        client_id: str = None
        client_secret: str = None
        grant_type: str = "client_credentials"
    )
)
```

Check the [Karrio Mutli-carrier SDK docs](https://docs.karrio.io) for Shipping API requests
