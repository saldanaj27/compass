# Compass - Personal AI Task Agent

## Project Overview
An AI-powered task management agent that helps users stay accountable to their goals. Built for personal use, designed to be extended into a multi-domain life management system.

## Current State (V1)
Basic CLI tool with:
- Goal and task management
- AI-powered goal breakdown
- Daily check-ins
- Simple completion tracking (done/not done, no hours)

## Tech Stack
- **Language**: Python 3.11+
- **AI**: Anthropic Claude API (Sonnet 4)
- **Database**: SQLite (local, simple, no auth needed)
- **CLI**: Click library
- **Future**: FastAPI web UI

## Architecture Philosophy
- **Start simple**: CLI-first, add web UI later
- **Local-first**: No cloud dependencies except Claude API
- **Completion-based**: Tasks are binary (done/not done), not time-based
- **Dogfooding**: Built for personal use, must actually be useful

## Code Style
- Type hints everywhere
- Clear function names (no abbreviations)
- Fail fast with helpful error messages
- Keep functions small (<30 lines)
- Comments only for "why", not "what"

## Database Schema
- **goals**: High-level objectives with deadlines
- **tasks**: Specific actions (completion-based, not hours)
- **daily_logs**: What was accomplished each day
- Priority over precision - simple is better

## Agent Design Principles
1. **Be helpful, not annoying**: Proactive but not pushy
2. **Learn patterns**: Track what user actually does vs plans
3. **No markdown in CLI**: Strip formatting for clean terminal output
4. **Context-aware**: Remember conversation history within session
5. **Conversational**: Natural language, not robotic

## Current Focus (Week 1-2)
- Core CRUD operations working smoothly
- Clean, usable CLI experience
- Agent can break down goals intelligently
- Daily check-in feels natural and useful

## Known Issues / TODO
- [ ] Tasks can't be edited (only deleted and recreated)
- [ ] No way to set task priority
- [ ] Daily logs don't link to specific tasks yet
- [ ] Agent doesn't remember context across sessions
- [ ] No weekly review feature yet

## Future Vision (V2+)
- Web UI for better visualization
- Calendar integration (Google Calendar)
- Proactive notifications (desktop/mobile)
- Pattern analysis ("you're most productive 9-11am")
- Multi-domain: finance, health, learning tracking
- Background agent that runs 24/7

## Testing Approach
- Manual testing via CLI (primary user is me)
- Add unit tests for database operations
- Integration tests for agent conversations
- Goal: 80%+ code coverage before V2

## Commands Reference
```bash
# Goals
add-goal <name> [--description] [--deadline]
list-goals
delete-goal <id>

# Tasks  
add-task <goal_id> <description> [--due]
list-tasks <goal_id>
done <task_id>
undone <task_id>
delete-task <task_id>

# Agent
checkin  # Daily check-in conversation
```

## Development Workflow
1. Use the tool daily (dogfooding)
2. Note what's annoying or missing
3. Build that feature next
4. Repeat

## Notes for AI Assistants
- This is a personal project, not enterprise software
- Optimize for "works well for one person" not "scales to millions"
- User is the developer, so rough edges are okay early on
- Focus on features that are immediately useful, not future-proofing
- When suggesting code, match the existing style exactly