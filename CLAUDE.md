# Compass — Development Guide

## What This Is

A personal AI accountability agent. CLI-first, local-first, conversation-driven. Users talk to Compass to set goals, get personalized tasks, and stay accountable through daily check-ins.

The agent learns about the user over time through a hybrid context system (global profile + goal-specific context).

## Architecture

```
main.py       — CLI entry point (Click), interactive mode, all commands
agent.py      — Claude API calls, system prompts, conversation management
database.py   — SQLite CRUD (goals, tasks, daily_logs)
user_profile.py — User profile management (~/.compass/user_profile.json)
```

### Key Design Patterns

**Interactive mode** (`compass` with no args): Opens a conversation loop. The agent gets a rich system prompt with all goals, tasks, overdue items, and profile data. Inline `/commands` handle actions (mark done, list tasks). Everything else goes to Claude as conversation.

**Conversational goal setup** (`compass new`): Discovery conversation asks clarifying questions before generating tasks. After conversation, agent extracts profile updates and saves them. Tasks are generated using both profile and goal-specific context.

**Hybrid context system**:
- `~/.compass/user_profile.json` — Global facts about the user (role, experience, strengths, weaknesses). Partitioned by category (career, health, finance, learning). Auto-updated from conversations.
- `goals.context` column — JSON blob with goal-specific context from the discovery conversation.
- Both are fed into prompts so the agent doesn't re-ask questions it already knows.

**conversation_turn()** — The central method for all multi-turn conversations. Takes message history + system prompt. Used by interactive mode, check-in, and goal discovery. The system prompt changes based on context.

## Database Schema

```sql
goals     — id, name, description, deadline, status, category, context, created_at
tasks     — id, goal_id, description, status, estimated_hours, due_date, created_at, completed_at
daily_logs — id, date, task_id, hours_spent, notes, created_at
```

The `context` column on goals stores JSON from the discovery conversation. The `category` column maps to profile categories (career, health, etc.).

Migration is handled inline in `create_tables()` with try/except ALTER TABLE calls.

## Code Style

- Type hints on function signatures
- Clear function names, no abbreviations
- Functions under 30 lines where possible
- Comments explain "why", not "what"
- No markdown in CLI output — `_clean_markdown()` strips it
- All prompts include current date via `_today()`
- Consistent 2-space indentation for CLI output

## Agent Personality

Direct and firm. Not a supportive coach. Asks pointed questions. Names avoidance when it sees it. Keeps responses to 2-4 sentences. Always ends with a question or next step. Plain conversational text, no formatting.

## Adding Features

When adding a new feature:
1. If it's a user action, add it as both a CLI subcommand AND an inline `/command` in `handle_inline_command()`
2. If it needs AI, add a method to `agent.py` with a focused system prompt
3. If it needs data, add methods to `database.py` (use try/except ALTER TABLE for migrations)
4. If it learns about the user, update the profile via `profile.update_category()`
5. Keep the interactive mode system prompt updated in `build_interactive_system_prompt()`

## Known Limitations

- No cross-session conversation memory (agent doesn't remember past check-ins)
- Profile learning is one-way (extracts from conversation, no manual editing of learned facts)
- No subtasks or task editing (delete and recreate)
- No weekly/monthly review features yet
- Exit keywords in conversation are exact match only ("done", "exit", "bye", "quit")

See `FUTURE.md` for the full roadmap.
