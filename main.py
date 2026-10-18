import argparse
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from agent import run_debugging_agent


console = Console()


def main():
    parser = argparse.ArgumentParser(
        description="RepoMedic - Agentic Codebase Debugger"
    )

    parser.add_argument(
        "--repo",
        required=True,
        help="Path to the repository you want RepoMedic to inspect.",
    )

    args = parser.parse_args()

    repo_path = Path(args.repo).resolve()

    if not repo_path.exists():
        console.print(
            f"[bold red]Error:[/bold red] Repository does not exist: "
            f"{repo_path}"
        )
        return

    if not repo_path.is_dir():
        console.print(
            "[bold red]Error:[/bold red] Repository path must be a directory."
        )
        return

    console.print(
        Panel.fit(
            "[bold cyan]RepoMedic[/bold cyan]\n"
            "Agentic Codebase Debugger",
            border_style="cyan",
        )
    )

    console.print(
        f"\n[bold]Repository:[/bold] {repo_path}\n"
    )

    bug_report = Prompt.ask(
        "[bold yellow]Describe the bug[/bold yellow]"
    )

    if not bug_report.strip():
        console.print(
            "[red]Bug description cannot be empty.[/red]"
        )
        return

    console.print(
        "\n[bold green]Starting investigation...[/bold green]\n"
    )

    result = run_debugging_agent(
        repo_path=str(repo_path),
        bug_report=bug_report,
    )

    console.print()

    console.print(
        Panel(
            result,
            title="[bold cyan]RepoMedic Debug Report[/bold cyan]",
            border_style="cyan",
        )
    )


if __name__ == "__main__":
    main()