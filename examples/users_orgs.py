"""Fetch user and organization information from the iGEM Registry API."""

import os

from dotenv import load_dotenv
from rich.console import Console
from rich.pretty import pprint

from igem_registry_api import Client, Organisation


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
    console = Console()

    # 1. Create an authenticated client instance
    client = Client()
    authenticate(client)

    # 2. Fetch user information
    user = client.me()
    console.rule("[bold]User Information[/bold]")
    pprint(user)

    # 3. Fetch user organizations
    orgs = user.affiliations(limit=2)
    console.rule("[bold]User Affiliations[/bold]")
    pprint(orgs)

    # 4. Fetch user parts
    parts = user.parts(limit=10)
    console.rule("[bold]User Parts[/bold]")
    pprint(parts)

    # 5. Fetch organization members
    for org in orgs:
        members = org.members()
        console.rule(f"[bold]Members of {org.name}[/bold]")
        pprint(members)

    # 6. Fetch most recent organizations
    recent = Organisation.fetch(
        client,
        limit=5,
        sort="audit.created",
        order="desc",
    )
    console.rule("[bold]Recent Organizations[/bold]")
    pprint(recent)
