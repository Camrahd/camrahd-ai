from camrahd_ai.config import config
from camrahd_ai.observability.logger import get_logger


logger = get_logger(__name__)


def get_llm():
  """Return the right LangChain LLM based on config."""
  provider = config["llm"]["provider"]
  model = config["llm"]["model"]
  logger.info(f"Using LLM provider: {provider}, model: {model}")


  if provider == "anthropic":
      from langchain_anthropic import ChatAnthropic
      return ChatAnthropic(model=model)

  if provider == "ollama":
      from langchain_ollama import ChatOllama
      return ChatOllama(model=model, base_url=config["llm"].get("base_url", "http://localhost:11434"))

  from langchain_openai import ChatOpenAI
  return ChatOpenAI(model=model)


def get_embedder():
  """Return the right LangChain embedder based on config."""
  provider = config["embeddings"]["provider"]
  model = config["embeddings"]["model"]
  logger.info(f"Using embeddings provider: {provider}, model: {model}")
  if provider == "huggingface":
      from langchain_huggingface import HuggingFaceEmbeddings
      return HuggingFaceEmbeddings(model_name=model)
  if provider == "ollama":
      from langchain_ollama import OllamaEmbeddings
      return OllamaEmbeddings(model=model, base_url=config["embeddings"].get("base_url", "http://localhost:11434"))
  from langchain_openai import OpenAIEmbeddings
  return OpenAIEmbeddings(model=model)




