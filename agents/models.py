import os

# Groq retires models regularly, so they're configurable without a code change.
# See https://console.groq.com/docs/models for the current list.
FAST_MODEL  = os.environ.get("GROQ_FAST_MODEL",  "openai/gpt-oss-20b")    # planner, writer
SMART_MODEL = os.environ.get("GROQ_SMART_MODEL", "openai/gpt-oss-120b")   # synthesizer, grader
