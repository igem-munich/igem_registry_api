"""TODO."""

import os

from dotenv import load_dotenv
from rich.pretty import pprint

from igem_registry_api import Client


def authenticate(client: Client) -> None:
    """Connect to the API and authenticate using environment variables."""
    client.connect()

    load_dotenv()
    username = os.getenv("IGEM_USERNAME")
    password = os.getenv("IGEM_PASSWORD")

    if username and password:
        client.sign_in(
            username=username,
            password=password,
        )


if __name__ == "__main__":
    client = Client()
    authenticate(client)

    user = client.me()

    pprint(user)

    orgs = user.affiliations()

    pprint(orgs)

    parts = user.parts()

    pprint(parts)
