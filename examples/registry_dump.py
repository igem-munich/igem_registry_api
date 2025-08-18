"""TODO."""

import json
from pathlib import Path

import brotli
from rich.console import Console
from rich.pretty import pprint

from igem_registry_api import Client, parts

DATA = Path("examples/data/registry.tar.br")


if __name__ == "__main__":
    """Dump iGEM Registry parts to a compressed file."""
    console = Console()

    # 1. Create a connected client instance
    client = Client()
    client.connect()

    # 2. Fetch all parts (ca. 45 min runtime)
    all_parts = parts(client, limit=50)

    pprint(all_parts)

    # 3. Save parts to a Brotli-compressed JSON file
    with DATA.open("wb") as file:
        data = json.dumps(all_parts, default=str).encode("utf-8")
        compressed = brotli.compress(data)
        file.write(compressed)
