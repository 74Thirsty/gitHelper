"""Modern Typer-based CLI for gitHelper."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .core import GitService
from .core.git import GitServiceError
from .core.github import GitHubService, GitHubServiceError
from .ui import CommandPalette, PaletteCommand
from .utils import ConfigManager, TokenManager, configure_logging
from .utils.token_manager import TokenManagerError

console = Console()
app = typer.Typer(help="gitHelper — modern Git and GitHub assistant")

PALETTE_COMMANDS: Dict[str, PaletteCommand] = {
    "onboard": PaletteCommand("onboard", "Run the guided onboarding experience."),
    "status": PaletteCommand("status", "Show the smart repository status dashboard."),
    "scan": PaletteCommand("scan", "Scan the working tree and highlight actionable insights."),
    "resolve": PaletteCommand("resolve", "Get recommended next steps for repository hygiene."),
    "codify": PaletteCommand("codify", "Summarise changes into human friendly notes."),
    "pushall": PaletteCommand("pushall", "Push every local branch with safety checks."),
    "devlog": PaletteCommand("devlog", "Print Git logs alongside GitHub events."),
    "diff-ai": PaletteCommand("diff-ai", "Generate AI-friendly diff summaries."),
    "settings": PaletteCommand("settings", "Review or update gitHelper configuration."),
}


def _git_service(path: Path) -> GitService:
    return GitService(path)


def _github_service(token_manager: TokenManager) -> Optional[GitHubService]:
    try:
        token = token_manager.require(scopes=["repo"], scope_provider=None)
    except TokenManagerError as exc:
        console.print(f"[yellow]{exc}[/yellow]")
        return None
    try:
        return GitHubService(token)
    except GitHubServiceError as exc:
        console.print(f"[red]{exc}[/red]")
        return None


@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", help="Enable debug logging."),
    gui: bool = typer.Option(False, "--gui", help="Attempt to launch the GUI fallback."),
) -> None:
    """Configure logging and bootstrap shared state."""

    configure_logging(verbose)
    ctx.obj = {
        "config": ConfigManager(),
        "token_manager": TokenManager(),
    }
    if gui:
        console.print(
            "[yellow]GUI mode is not yet implemented. Falling back to the enhanced CLI experience.[/yellow]"
        )
    console.print(f"[bold cyan]gitHelper[/bold cyan] v{__version__}")


@app.command()
def palette(ctx: typer.Context) -> None:
    """Launch the fuzzy command palette."""

    palette = CommandPalette(PALETTE_COMMANDS)
    console.print(Panel(palette.format_help(), title="Command Palette"))
    selection = palette.choose()
    if not selection:
        console.print("[yellow]No command selected.[/yellow]")
        return
    console.print(f"[green]Running[/green] [bold]{selection.name}[/bold]…")
    handler = COMMAND_HANDLERS.get(selection.name)
    if handler is None:
        console.print(f"[red]No handler registered for {selection.name}.[/red]")
        return
    handler(ctx)

def onboard_command(ctx: typer.Context) -> None:
    """Interactive onboarding to configure tokens and preferences."""

    config: ConfigManager = ctx.obj["config"]
    token_manager: TokenManager = ctx.obj["token_manager"]
    console.print(Panel("Let's configure gitHelper for your GitHub workflow!", title="Onboarding"))
    default_org = typer.prompt("Default GitHub organisation", default=config.get("github", "default_org", ""))
    editor = typer.prompt("Preferred editor command", default=config.get("editor", "command"))
    theme = typer.prompt("Theme (system/light/dark)", default=config.get("ui", "theme", "system"))
    use_gui = typer.confirm("Enable GUI fallback when available?", default=config.get("ui", "use_gui", False))
    config.set("github", "default_org", default_org)
    config.set("editor", "command", editor)
    config.set("ui", "theme", theme)
    config.set("ui", "use_gui", use_gui)

    if typer.confirm("Would you like to store a GitHub Personal Access Token now?", default=True):
        token = typer.prompt("Enter GitHub token", hide_input=True)
        try:
            token_manager.save(token)
        except TokenManagerError as exc:
            console.print(f"[red]{exc}[/red]")
        else:
            service = _github_service(token_manager)
            if service:
                try:
                    login = service.current_user()
                    console.print(f"[green]Authenticated as[/green] [bold]{login}[/bold]")
                except GitHubServiceError as exc:  # pragma: no cover - network behaviour
                    console.print(f"[yellow]{exc}[/yellow]")
            console.print("[green]Token stored securely in system keyring.[/green]")
    console.print(Panel(config.profile_summary(), title="Configuration saved"))


def status_command(
    ctx: typer.Context,
    path: Path = typer.Option(Path.cwd(), "--path", exists=True, file_okay=False, help="Repository path."),
) -> None:
    """Show a dashboard summarising repository status."""

    service = _git_service(path)
    try:
        snapshot = service.status()
    except GitServiceError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)
    table = Table(title="Repository status", box=None)
    table.add_column("Metric", justify="left")
    table.add_column("Value", justify="right")
    table.add_row("Branch", snapshot.branch)
    table.add_row("Detached", "yes" if snapshot.detached else "no")
    table.add_row("Ahead", str(snapshot.ahead))
    table.add_row("Behind", str(snapshot.behind))
    table.add_row("Staged", str(snapshot.staged))
    table.add_row("Unstaged", str(snapshot.unstaged))
    table.add_row("Untracked", str(snapshot.untracked))
    table.add_row("Stashes", str(snapshot.stashes))
    table.add_row("Clean", "yes" if snapshot.clean else "no")
    console.print(Panel(table, title=str(path)))


def scan_command(
    ctx: typer.Context,
    path: Path = typer.Option(Path.cwd(), "--path", exists=True, file_okay=False),
) -> None:
    """Scan the repository and surface actionable insights."""

    service = _git_service(path)
    try:
        data = service.scan()
    except GitServiceError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)
    console.print(Panel(f"Branches: {', '.join(data['branches']) or 'none'}", title="Local branches"))
    console.print(Panel(f"Remotes: {', '.join(data['remotes']) or 'none'}", title="Remotes"))
    console.print(Panel(f"Stashes: {len(data['stashes'])}", title="Stashes"))
    if data["pending_commits"]:
        console.print(Panel("\n".join(data["pending_commits"]), title="Commits not on origin"))
    recommendations = service.recommend_resolution_actions()
    console.print(Panel("\n".join(recommendations), title="Suggested actions"))


def resolve_command(
    ctx: typer.Context,
    path: Path = typer.Option(Path.cwd(), "--path", exists=True, file_okay=False),
) -> None:
    """Offer resolution strategies based on repository state."""

    service = _git_service(path)
    recommendations = service.recommend_resolution_actions()
    console.print(Panel("\n".join(recommendations), title="Resolution guide"))


def codify_command(
    ctx: typer.Context,
    path: Path = typer.Option(Path.cwd(), "--path", exists=True, file_okay=False),
) -> None:
    """Summarise staged and unstaged changes for commit messaging."""

    service = _git_service(path)
    summary = service.summarize_changes()
    console.print(Panel(summary, title="Change summary"))


def pushall_command(
    ctx: typer.Context,
    path: Path = typer.Option(Path.cwd(), "--path", exists=True, file_okay=False),
    remote: str = typer.Option("origin", "--remote", help="Remote to push to."),
    execute: bool = typer.Option(False, "--execute", help="Actually run the push."),
    force: bool = typer.Option(False, "--force", help="Use --force-with-lease when pushing."),
) -> None:
    """Push every local branch to the specified remote."""

    service = _git_service(path)
    console.print(Panel("\n".join(service.branches_with_upstream()), title="Branch -> upstream mapping"))
    if not execute:
        console.print(
            "[yellow]Dry run only. Re-run with --execute to push branches. --force adds --force-with-lease.[/yellow]"
        )
        return
    results = service.auto_push_all(remote=remote, force=force)
    lines = []
    for result in results:
        status_text = "ok" if result.returncode == 0 else f"failed ({result.stderr.strip()})"
        lines.append(f"git {' '.join(result.args)} -> {status_text}")  # type: ignore[arg-type]
    console.print(Panel("\n".join(lines) or "No branches to push.", title="Push summary"))


def devlog_command(
    ctx: typer.Context,
    path: Path = typer.Option(Path.cwd(), "--path", exists=True, file_okay=False),
    limit: int = typer.Option(5, "--limit", help="Number of commits/events to show."),
) -> None:
    """Display Git history with optional GitHub events."""

    service = _git_service(path)
    token_manager: TokenManager = ctx.obj["token_manager"]
    events: list[str] = []
    github = _github_service(token_manager)
    if github and typer.confirm("Fetch GitHub events as well?", default=False):
        config: ConfigManager = ctx.obj["config"]
        default_org = config.get("github", "default_org", "")
        repo_hint = typer.prompt("Repository (owner/name)", default=default_org)
        try:
            events = github.recent_events(repo_hint, limit=limit)
        except GitHubServiceError as exc:  # pragma: no cover - network
            console.print(f"[yellow]{exc}[/yellow]")
    console.print(Panel(service.format_devlog(limit=limit, github_events=events), title="Dev log"))


def mock_command(ctx: typer.Context) -> None:
    """Run gitHelper in dry-run mode for experimentation."""

    console.print(
        Panel(
            "Mock mode enables safe experimentation. All Git operations stay in dry-run preview until you re-run without --mock.",
            title="Mock mode",
        )
    )


def diff_ai_command(
    ctx: typer.Context,
    path: Path = typer.Option(Path.cwd(), "--path", exists=True, file_okay=False),
) -> None:
    """Produce AI-ready summaries of recent diffs."""

    service = _git_service(path)
    summary = service.summarize_changes()
    console.print(Panel(summary, title="AI-ready diff summary"))
    console.print(
        "[dim]Use this summary as context for LLMs such as OpenAI GPT models. Ensure secrets are removed before sharing.[/dim]"
    )


def settings_command(ctx: typer.Context) -> None:
    """Show current configuration and token status."""

    config: ConfigManager = ctx.obj["config"]
    token_manager: TokenManager = ctx.obj["token_manager"]
    github = _github_service(token_manager)
    scope_provider = github.ensure_scopes if github else None
    description = token_manager.describe(scope_provider=scope_provider) if scope_provider else token_manager.describe()
    console.print(Panel(config.profile_summary(), title="Profile"))
    console.print(Panel(description, title="GitHub token"))


def _register_commands() -> Dict[str, Callable[[typer.Context], None]]:
    command_map: Dict[str, Callable[[typer.Context], None]] = {}
    command_map["onboard"] = app.command()(onboard_command)
    command_map["status"] = app.command()(status_command)
    command_map["scan"] = app.command()(scan_command)
    command_map["resolve"] = app.command()(resolve_command)
    command_map["codify"] = app.command()(codify_command)
    command_map["pushall"] = app.command()(pushall_command)
    command_map["devlog"] = app.command(name="devlog")(devlog_command)
    command_map["mock"] = app.command()(mock_command)
    command_map["diff-ai"] = app.command(name="diff-ai")(diff_ai_command)
    command_map["settings"] = app.command()(settings_command)
    return command_map


COMMAND_HANDLERS = _register_commands()


def main_entry() -> None:
    app()


def main() -> None:  # pragma: no cover - entry point
    main_entry()
