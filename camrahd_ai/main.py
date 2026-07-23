import asyncio
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt


from camrahd_ai.config import config
from camrahd_ai.context.indexers.factory import get_indexer, get_index_inspector
from camrahd_ai.llm.factory import get_llm, get_embedder
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from camrahd_ai.agent.factory import build_agent
from camrahd_ai.memory.short_term import get_checkpointer_db_path
from camrahd_ai.agent.orchestrator import stream_query
from camrahd_ai.memory.session import get_current_session, new_session, switch_session
from camrahd_ai.observability.logger import get_logger


# Search for .env from the launch directory upward, never the install location.
load_dotenv()
load_dotenv(Path.home() / ".config" / "camrahd" / ".env")


console = Console()
logger = get_logger(__name__)


async def ask(agent, question: str, session_id: str) -> None:
   """Stream the agent's answer to the console token by token."""
   try:
       async for token in stream_query(agent, question, session_id):
           console.print(token, end="", markup=False, highlight=False)
       console.print()
   except Exception as e:
       logger.error(f"Agent error: {e}")
       console.print(f"\n[red]Error:[/red] {e}")




def get_or_create_index():
   repo_path = str(Path.cwd())
   logger.info(f"Checking index for: {repo_path}")
   console.print(f"[dim]Checking index for {repo_path}...[/dim]")
   return get_indexer()(repo_path)




async def initialize(checkpointer):
   """Bootstrap LLM, embedder, index, MCP tools, and session before the REPL starts."""
   llm = get_llm()
   embedder = get_embedder()
   console.print(f"[dim]LLM: {config['llm']['provider']} / {config['llm']['model']}[/dim]")
   console.print(f"[dim]Embedder: {config['embeddings']['provider']} / {config['embeddings']['model']}[/dim]")




   index = get_or_create_index()
   agent = await build_agent(checkpointer)
   session_id = get_current_session()
   console.print(f"[dim]Session: {session_id}[/dim]")
   console.print(f"[green]✓ Ready[/green]\n")
   return llm, embedder, index, agent, session_id




async def _run_async():
   logger.info("Starting Camrahd AI")
   console.print("\n[bold blue]Camrahd AI[/bold blue] — RAG-powered code assistant")


   async with AsyncSqliteSaver.from_conn_string(get_checkpointer_db_path()) as checkpointer:
       llm, embedder, index, agent, session_id = await initialize(checkpointer)
       console.print("Just type a question, or [bold]'/exit'[/bold] to quit\n")


       while True:
           user_input = Prompt.ask("[bold green]>[/bold green]")


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
           elif user_input == "/new_session":
               session_id = new_session()
               console.print(f"[green]New session started: {session_id}[/green]")
           elif user_input.startswith("/switch "):
               target = user_input.removeprefix("/switch ").strip()
               session_id = switch_session(target)
               console.print(f"[green]Switched to session: {session_id}[/green]")
           elif user_input == "/session":
               console.print(f"[dim]Current session: {session_id}[/dim]")
           elif user_input == "/show_index":
               logger.info("Showing index")
               get_index_inspector()(index)
           else:
               logger.warning(f"Unknown command received: {user_input}")
               console.print("[yellow]Unknown command. Try:[/yellow]")
               console.print("  [bold]<question>[/bold]               — just type to ask about the codebase")
               console.print("  [bold]/show_index[/bold]              — show all chunks in the index")
               console.print("  [bold]/new_session[/bold]             — start a fresh conversation")
               console.print("  [bold]/switch <session_id>[/bold]     — resume a past session")
               console.print("  [bold]/session[/bold]                 — show current session id")


def run():
   asyncio.run(_run_async())




if __name__ == "__main__":
   run()
