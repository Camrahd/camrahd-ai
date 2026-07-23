from camrahd_ai.config import config


class UsageTracker:
   """Accumulate token usage (and optional cost) for the current session."""

   def __init__(self):
       self.input_tokens = 0
       self.output_tokens = 0
       self.requests = 0

   def add_from_chunk(self, chunk) -> None:
       """Record usage_metadata from a streamed message chunk, if present."""
       usage = getattr(chunk, "usage_metadata", None)
       if not usage:
           return
       self.input_tokens += usage.get("input_tokens", 0)
       self.output_tokens += usage.get("output_tokens", 0)
       self.requests += 1

   def cost(self) -> float | None:
       """Session cost in dollars, if pricing is configured in camrahd.yaml.

       pricing:
         input_per_1m: 2.50    # $ per million input tokens
         output_per_1m: 10.00  # $ per million output tokens
       """
       pricing = config.get("pricing")
       if not pricing:
           return None
       return (
           self.input_tokens / 1_000_000 * pricing.get("input_per_1m", 0)
           + self.output_tokens / 1_000_000 * pricing.get("output_per_1m", 0)
       )

   def summary(self) -> str:
       text = (
           f"tokens: {self.input_tokens:,} in / {self.output_tokens:,} out "
           f"({self.requests} LLM calls)"
       )
       cost = self.cost()
       if cost is not None:
           text += f" — ${cost:.4f}"
       return text


tracker = UsageTracker()
