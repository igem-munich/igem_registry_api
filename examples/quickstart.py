"""Quickstart example: connect, authenticate, and opt-in.

This example demonstrates how to quickly get started with the iGEM Registry API
by connecting to the API, authenticating, and opting in to be a contributor.

To not expose sensitive information, such as user credentials, it's recommended
to use environment variables for configuration. Store your API credentials in
a untracked `.env` file and load them using `dotenv` package.
"""

import os

from dotenv import load_dotenv
from rich.pretty import pprint

from igem_registry_api import Client


def main() -> None:
    """Prepare to work with the iGEM Registry API client."""
    # 1. Create a client instance
    client = Client()

    # 2. Connect to the API
    client.connect()

    # 3. Authenticate using environment variables
    load_dotenv()
    username = os.getenv("IGEM_USERNAME")
    password = os.getenv("IGEM_PASSWORD")

    if username and password:
        client.sign_in(
            username=username,
            password=password,
        )

    # 4. Opt-in to be a contributor
    if not client.is_opted_in:
        client.opt_in()

    # 5. Test user settings
    pprint(client.me())


if __name__ == "__main__":
    main()
