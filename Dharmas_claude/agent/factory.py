from langchain.agents import create_agent


from Dharmas_claude.llm.factory import get_llm
from Dharmas_claude.agent.tools import search_codebase
from Dharmas_claude.observability.logger import get_logger
from Dharmas_claude.tools.terminal_tools import run_command, run_in_directory
from Dharmas_claude.mcp.mcp_client import get_mcp_tools


logger = get_logger(__name__)


SYSTEM_PROMPT = """You are a senior software engineer with deep knowledge of the codebase.
Always use the search_codebase tool before answering any question.
Reference specific file names, function names and line numbers in your answers.
If you cannot find the answer in the codebase, say so explicitly."""




async def build_agent(checkpointer):
   """Create and return a LangChain agent with persistent memory."""
   llm = get_llm()
   mcp_tools = await get_mcp_tools()
   tools = [
       search_codebase,
       run_command,
       run_in_directory,
       *mcp_tools,
   ]


   return create_agent(
       llm,
       tools=tools,
       system_prompt=SYSTEM_PROMPT,
       checkpointer=checkpointer,
   )
