import asyncio
import shutil
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich import box
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.spinner import Spinner
from rich.table import Table


from camrahd_ai.config import config
from camrahd_ai.context.indexers.factory import get_indexer, get_index_inspector
from camrahd_ai.llm.factory import get_llm, get_embedder
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from camrahd_ai.agent.factory import build_agent
from camrahd_ai.memory.short_term import get_checkpointer_db_path
from camrahd_ai.agent.orchestrator import stream_query
from camrahd_ai.memory.session import get_current_session, list_sessions, new_session, switch_session
from camrahd_ai.observability.logger import get_logger
from camrahd_ai.observability.usage import tracker


# Search for .env from the launch directory upward, never the install location.
load_dotenv()
load_dotenv(Path.home() / ".config" / "camrahd" / ".env")


console = Console()
logger = get_logger(__name__)


def _answer_panel(buffer: str) -> Panel:
   return Panel(
       Markdown(buffer),
       title="[bold blue]Camrahd[/bold blue]",
       title_align="left",
       border_style="blue",
       box=box.ROUNDED,
       padding=(0, 1),
   )


async def ask(agent, question: str, session_id: str) -> None:
   """Stream the agent's answer into a live Markdown panel."""
   buffer = ""
   try:
       with Live(console=console, refresh_per_second=8, vertical_overflow="visible") as live:
           live.update(Spinner("dots", text="[dim]Thinking…[/dim]", style="blue"))
           async for token in stream_query(agent, question, session_id):
               buffer += token
               live.update(_answer_panel(buffer))
   except (KeyboardInterrupt, asyncio.CancelledError):
       console.print("\n[dim]Interrupted.[/dim]")
       return
   except Exception as e:
       logger.error(f"Agent error: {e}")
       console.print(f"\n[red]Error:[/red] {e}")
       return
   console.print(f"[dim]{tracker.summary()}[/dim]", justify="right")


_COMMANDS = [
   ("<question>", "just type to ask about the codebase"),
   ("/help", "show this help"),
   ("/show_index", "show all chunks in the index"),
   ("/new_session", "start a fresh conversation"),
   ("/sessions", "list all past sessions"),
   ("/switch <session_id>", "resume a past session"),
   ("/session", "show current session id"),
   ("/model \\[name]", "show or switch the LLM model"),
   ("/usage", "show session token usage"),
   ("/exit", "quit"),
]


def print_help() -> None:
   table = Table(title="Commands", box=box.ROUNDED, border_style="dim", title_style="bold")
   table.add_column("Command", style="bold cyan", no_wrap=True)
   table.add_column("Description")
   for command, description in _COMMANDS:
       table.add_row(command, description)
   console.print(table)




def get_or_create_index():
   repo_path = str(Path.cwd())
   logger.info(f"Checking index for: {repo_path}")
   with console.status(f"[dim]Indexing {repo_path}…[/dim]", spinner="dots"):
       return get_indexer()(repo_path)


def print_banner(session_id: str, repo_path: str) -> None:
   info = Table.grid(padding=(0, 2))
   info.add_column(style="bold dim", no_wrap=True)
   info.add_column()
   info.add_row("LLM", f"{config['llm']['provider']} / {config['llm']['model']}")
   info.add_row("Embedder", f"{config['embeddings']['provider']} / {config['embeddings']['model']}")
   info.add_row("Repo", repo_path)
   info.add_row("Session", session_id)
   console.print(Panel(
       info,
       title=f"[bold blue]Camrahd AI[/bold blue] [dim]v{_get_version()}[/dim]",
       subtitle="[green]✓ ready[/green]",
       border_style="blue",
       box=box.ROUNDED,
       expand=False,
   ))
   console.print("[dim]Type a question, or /help for commands.[/dim]")




async def initialize(checkpointer):
   """Bootstrap LLM, embedder, index, MCP tools, and session before the REPL starts."""
   llm = get_llm()
   embedder = get_embedder()
   index = get_or_create_index()
   agent = await build_agent(checkpointer)
   session_id = get_current_session()
   print_banner(session_id, str(Path.cwd()))
   return llm, embedder, index, agent, session_id




async def _run_async():
   logger.info("Starting Camrahd AI")


   async with AsyncSqliteSaver.from_conn_string(get_checkpointer_db_path()) as checkpointer:
       llm, embedder, index, agent, session_id = await initialize(checkpointer)


       while True:
           try:
               user_input = Prompt.ask("\n[bold cyan]❯[/bold cyan]")
           except (KeyboardInterrupt, EOFError):
               console.print("\n[dim]Goodbye![/dim]")
               break


           if not user_input.strip():
               continue
           if not user_input.startswith("/"):
               # Plain text is a question — no /ask prefix needed.
               question = user_input.strip()
               logger.info(f"Question received: {question}")
               await ask(agent, question, session_id)
           elif user_input.lower() in ("/exit", "/quit"):
               logger.info("Shutting down")
               console.print("[dim]Goodbye![/dim]")
               break
           elif user_input.startswith("/ask "):
               # Kept for backwards compatibility; plain text works too.
               question = user_input.removeprefix("/ask ").strip()
               logger.info(f"Ask command received: {question}")
               await ask(agent, question, session_id)
           elif user_input == "/help":
               print_help()
           elif user_input == "/new_session":
               session_id = new_session()
               console.print(f"[green]New session started: {session_id}[/green]")
           elif user_input == "/sessions":
               sessions = list_sessions()
               if not sessions:
                   console.print("[dim]No past sessions found.[/dim]")
               else:
                   table = Table(title="Sessions", box=box.ROUNDED, border_style="dim", title_style="bold")
                   table.add_column("Session id", style="cyan")
                   table.add_column("")
                   for sid in sessions:
                       table.add_row(sid, "[green]current[/green]" if sid == session_id else "")
                   console.print(table)
           elif user_input.startswith("/model"):
               parts = user_input.split(maxsplit=2)
               if len(parts) == 1:
                   console.print(f"[dim]Current model: {config['llm']['provider']} / {config['llm']['model']}[/dim]")
               else:
                   # /model <name> or /model <provider> <name>
                   if len(parts) == 3:
                       config["llm"]["provider"] = parts[1]
                       config["llm"]["model"] = parts[2]
                   else:
                       config["llm"]["model"] = parts[1]
                   agent = await build_agent(checkpointer)
                   console.print(f"[green]Switched to {config['llm']['provider']} / {config['llm']['model']}[/green]")
           elif user_input.startswith("/switch "):
               target = user_input.removeprefix("/switch ").strip()
               session_id = switch_session(target)
               console.print(f"[green]Switched to session: {session_id}[/green]")
           elif user_input == "/session":
               console.print(f"[dim]Current session: {session_id}[/dim]")
           elif user_input == "/usage":
               console.print(f"[dim]Session usage — {tracker.summary()}[/dim]")
           elif user_input == "/show_index":
               logger.info("Showing index")
               get_index_inspector()(index)
           else:
               logger.warning(f"Unknown command received: {user_input}")
               console.print("[yellow]Unknown command.[/yellow]")
               print_help()


def _get_version() -> str:
   try:
       return version("camrahd-ai")
   except PackageNotFoundError:
       return "0.0.0-dev"


cli = typer.Typer(add_completion=False, invoke_without_command=True, no_args_is_help=False)


@cli.callback()
def main(
   ctx: typer.Context,
   show_version: bool = typer.Option(False, "--version", "-V", help="Print version and exit."),
):
   """Camrahd AI — RAG-powered terminal code assistant."""
   if show_version:
       console.print(f"camrahd {_get_version()}")
       raise typer.Exit()
   if ctx.invoked_subcommand is None:
       chat()


@cli.command()
def chat():
   """Start the interactive chat REPL (default)."""
   try:
       asyncio.run(_run_async())
   except KeyboardInterrupt:
       console.print("\n[dim]Goodbye![/dim]")


@cli.command()
def init():
   """Create a starter camrahd.yaml config in the current directory."""
   target = Path.cwd() / "camrahd.yaml"
   if target.exists():
       console.print(f"[yellow]{target} already exists — leaving it untouched.[/yellow]")
       raise typer.Exit(code=1)
   shutil.copy(Path(__file__).parent / "config.yaml", target)
   console.print(f"[green]Created {target}[/green]")
   console.print("[dim]Edit it to pick your provider/model, and set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env[/dim]")


def run():
   cli()




if __name__ == "__main__":
   run()
