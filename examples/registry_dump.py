"""Dump iGEM Registry parts to a compressed file with a live progress bar."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from queue import Queue
from typing import TYPE_CHECKING

import brotli
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from igem_registry_api import Client, Part, dump

if TYPE_CHECKING:
    from collections.abc import Callable


DATA = Path("examples/data/parts.tar.br")


def progress_notify(queue: Queue[tuple[int, int | None]]) -> Callable:
    """Create a progress notification function.

    Args:
        queue (Queue[tuple[int, int | None]]): A queue to send progress
            updates.

    Returns:
        Callable: A function that sends progress updates to the queue.

    """

    def notify(current: int, total: int | None) -> None:
        queue.put((current, total))

    return notify


def progress_render(queue: Queue[tuple[int, int | None]]) -> None:
    """Render a progress bar that tracks absolute part counts.

    Arg:
        queue (Queue[tuple[int, int | None]]): A queue to receive progress
            updates.
    """
    console = Console()
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold]Fetching parts[/bold]"),
        BarColumn(),
        MofNCompleteColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        transient=True,
        console=console,
    ) as progress:
        task = progress.add_task("Fetching parts", total=None)

        while True:
            msg = queue.get()
            if msg is None:
                break

            current, total = msg
            if total is not None:
                progress.update(task, completed=current, total=total)
            else:
                progress.update(task, completed=current)


if __name__ == "__main__":
    console = Console()

    # 1. Set up client
    client = Client()
    client.connect()

    # 2. Set up progress tracking thread
    queue: Queue = Queue()
    notify = progress_notify(queue)

    progress = threading.Thread(
        target=progress_render,
        args=(queue,),
        daemon=True,
    )
    progress.start()

    # 3. Fetch parts (main thread)
    try:
        all_parts = Part.fetch(client, limit=None, progress=notify)
    finally:
        queue.put(None)
        progress.join()

    # 4. Save to Brotli-compressed JSON
    DATA.parent.mkdir(parents=True, exist_ok=True)
    with DATA.open("wb") as file:
        data = json.dumps(
            all_parts,
            indent=2,
            default=dump(),
        ).encode("utf-8")
        file.write(brotli.compress(data))

    console.print(f"[green]Wrote[/green] {DATA} ({len(all_parts):,} parts)")
