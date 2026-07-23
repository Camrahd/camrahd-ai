from rich.console import Console
from rich.prompt import Confirm


from camrahd_ai.config import config
from camrahd_ai.observability.logger import get_logger


logger = get_logger(__name__)
console = Console()


def approval_required() -> bool:
   return config.get("tools", {}).get("require_approval", True)


def request_approval(description: str) -> bool:
   """Show the user what the agent wants to do and ask for permission.

   Returns True if approved. When tools.require_approval is false in
   config, everything is auto-approved.
   """
   if not approval_required():
       return True
   console.print(f"\n[yellow]⚠ Agent wants to:[/yellow] [bold]{description}[/bold]")
   approved = Confirm.ask("Allow?", default=False)
   if not approved:
       logger.info(f"User denied tool call: {description}")
   return approved


DENIED = "Error: the user denied this action. Ask them before retrying."
