"""TODO."""

from rich.console import Console
from rich.pretty import pprint

from igem_registry_api import Category, Client, License, Type


def main() -> None:
    """TODO."""
    console = Console()

    # 1. Set up client
    client = Client()
    client.connect()

    # 2. Fetch all part types
    part_types = Type.fetch(
        client,
        sort="label",
        order="desc",
    )
    console.rule("[bold]Part Types[/bold]")
    pprint(part_types)

    # 3. Fetch some part categories
    part_categories = Category.fetch(
        client,
        sort="label",
        limit=25,
    )
    console.rule("[bold]Part Categories[/bold]")
    pprint(part_categories)

    # 4. Fetch all part licenses
    part_licenses = License.fetch(
        client,
        sort="description",
    )
    console.rule("[bold]Part Licenses[/bold]")
    pprint(part_licenses)


if __name__ == "__main__":
    main()
