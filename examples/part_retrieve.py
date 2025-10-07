"""Fetch and display parts information from the iGEM Registry."""

from __future__ import annotations

from rich.console import Console
from rich.pretty import pprint

from igem_registry_api import Client, Part
from igem_registry_api.part import Reference


def main() -> None:
    """Search and retrieve parts with their associated information."""
    console = Console()

    # 1. Set up client
    client = Client()
    client.connect()

    # 2. Search for parts
    console.rule("[bold]Search Parts[/bold]")
    parts = Part.search(
        client,
        query="RBS based on Elowitz repressilator.",
        limit=5,
    )

    # 3. Extract the oldest part
    elowitz = parts[-1]
    pprint(elowitz)

    # 4. Display usage and twin information
    console.print(
        f"Number of uses: {elowitz.uses}",
        f"Number of twins: {len(elowitz.twins)}",
        sep="\n",
    )

    # 5. Retrieve a specific part by its slug
    console.rule("[bold]Retrieve Part[/bold]")
    part = Part.get(
        client,
        Reference(slug="bba-25k0ccj6"),
    )

    # 6. Load additional part details
    part.load_composition()
    part.load_authors()
    part.load_annotations()

    # 7. Display part details
    pprint(part)
    console.print(f"[green]Composite status:[/green] {part.is_composite}")
    console.print("[green]Sequence:[/green]")
    pprint(part.sequence)
    console.print("[green]Compatibilities:[/green]")
    pprint(part.compatibilities)


if __name__ == "__main__":
    main()
