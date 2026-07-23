from typing import AsyncIterator

from langchain_core.messages import AIMessageChunk

from camrahd_ai.agent.factory import build_agent
from camrahd_ai.observability.logger import get_logger
from camrahd_ai.observability.usage import tracker


logger = get_logger(__name__)


def _chunk_text(chunk: AIMessageChunk) -> str:
  """Extract plain text from a message chunk (str or content-block list)."""
  content = chunk.content
  if isinstance(content, str):
      return content
  if isinstance(content, list):
      return "".join(
          block.get("text", "") for block in content
          if isinstance(block, dict) and block.get("type") == "text"
      )
  return ""


async def stream_query(agent, question: str, thread_id: str) -> AsyncIterator[str]:
  """Stream the agent's answer token by token as it is generated."""
  logger.info(f"Streaming query for session {thread_id}: {question}")
  agent_config = {"configurable": {"thread_id": thread_id}}
  async for chunk, _metadata in agent.astream(
      {"messages": [{"role": "user", "content": question}]},
      agent_config,
      stream_mode="messages",
  ):
      if isinstance(chunk, AIMessageChunk):
          tracker.add_from_chunk(chunk)
          text = _chunk_text(chunk)
          if text:
              yield text


async def handle_query(agent, question: str, thread_id: str) -> str:
  """Entry point for all user queries - invokes the agent."""
  logger.info(f"Handling query for session {thread_id}: {question}")
  agent_config = {"configurable": {"thread_id": thread_id}}
  try:
      response = await agent.ainvoke({"messages": [{"role": "user", "content": question}]}, agent_config)
      return response["messages"][-1].content
  except Exception as e:
      logger.error(f"Agent error: {e}")
      return f"Error: {e}"

