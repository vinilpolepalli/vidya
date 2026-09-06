"""syllabot: the deterministic middle of a course-deadline bot.

LLM at the edges, code in the middle. The bot's model reads pages and applies
calendar operations through plugins. Everything between those two points --
normalizing items, parsing dates, diffing against last night's belief, guarding
against destructive writes, gating the plan, keeping the ledger idempotent --
is plain Python here, covered by a fixture suite.
"""

__version__ = "0.1.0"
