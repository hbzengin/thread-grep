import typer
from rich import print
from pathlib import Path
from .search import search_all
import time


app = typer.Typer()


@app.command()
def search(path: str, query: str, max_workers: int) -> None:
    """
    Look for a specific query in files at the given path
    path: The directory path to search in
    query: The string to search for in the files
    """
    cwd = Path.cwd()
    dir = cwd / path
    exists = Path.exists(dir)

    if not exists:
        print(f"[red]ERROR:[/red] Path [yellow]{dir}[/yellow] does not exist")
        exit(1)

    print(
        f'[yellow]LOG:[/yellow] Starting a search in [green]"{dir}"[/green] for [green]"{query}"[/green]'
    )

    start_time = time.time()
    search_all(str(dir), query, max_workers)
    
    print(
        f"[yellow]LOG:[/yellow] Execution ended in {time.time() - start_time} seconds"
    )


def main() -> None:
    app()
