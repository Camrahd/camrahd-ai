from langchain.agents import create_agent
from educosys_claude.llm.factory import get_llm
from educosys_claude.agent.tools import search_codebase
from educosys_claude.memory.short_term import get_checkpointer, get_summarization_middleware
from educosys_claude.observability.logger import get_logger


logger = get_logger(__name__)


SYSTEM_PROMPT = """You are a senior software engineer with deep knowledge of the codebase.
Always use the search_codebase tool before answering any question.
Reference specific file names, function names and line numbers in your answers.
If you cannot find the answer in the codebase, say so explicitly."""


def build_agent():
   """Create and return a LangChain agent with persistent memory."""
   llm = get_llm()
   tools = [search_codebase]
   checkpointer = get_checkpointer()
   middleware = get_summarization_middleware()


   return create_agent(
       llm,
       tools=tools,
       system_prompt=SYSTEM_PROMPT,
       checkpointer=checkpointer,
       middleware=[middleware],
   )
