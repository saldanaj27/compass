# Compass

An AI agent that keeps you accountable to your goals.

Compass isn't a task manager. It's a personal AI agent that learns about you, understands your specific situation, and holds you accountable through direct, honest conversations.

You talk to it. It remembers. It pushes back when you're slacking. It knows your goals, your deadlines, and your weak spots — because you told it, and it didn't forget.

## What It Looks Like

```
$ compass

  compass

  Hey Javier. Here's where things stand:

  Goals:
    Land FAANG Job (3/8 tasks) — due 2026-04-30
    Master System Design (1/5 tasks)

  Tasks: 2 due today | 1 overdue | 10 active

  Talk to me, or type /help for commands.

  > I haven't touched the system design stuff in a week

  You said system design was your biggest weakness three weeks ago.
  What specifically is making you avoid it?

  > I don't know where to start, it feels overwhelming

  Start with one thing: pick a single system (URL shortener, chat app)
  and design it on paper for 30 minutes. No pressure to get it right.
  Can you do that today?

  > yeah I can do that after lunch

  Good. I'll ask you about it next time. Which system are you picking?

  > URL shortener

  Solid choice, it's a classic starter. Go do it after lunch.

  > /done 12

  Done! Task 12 marked complete.

  > quit

  See you.
```

## Why Compass

**It remembers you.** Your profile builds automatically from conversations. Tell it you're weak on system design once — it won't ask again, but it will hold you to improving it.

**It's direct.** No "great job!" for doing the bare minimum. Compass asks what's blocking you, calls out avoidance, and pushes you to be specific about commitments.

**It's personal.** When you add a goal, Compass asks about YOUR situation before generating tasks. Not generic "study 20 hours of algorithms" — specific tasks based on your experience, weaknesses, and timeline.

**It's local.** Your data stays on your machine in a SQLite database. Only API calls go to Anthropic's Claude for conversation. No accounts, no cloud sync, no tracking.

## Quick Start

### Prerequisites

- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/)

### Install

```bash
git clone https://github.com/yourusername/compass.git
cd compass

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install
pip install -e .

# Set up your API key
echo "ANTHROPIC_API_KEY=your-key-here" > .env
```

### Run

```bash
# Open interactive mode (the main experience)
compass

# Or jump straight to a specific action
compass status          # Quick dashboard
compass checkin         # Daily check-in conversation
compass new             # Create a new goal
```

## How It Works

### 1. Create a Goal

When you create a goal, Compass doesn't just add it to a list. It starts a conversation to understand your situation:

```
$ compass new "Land a FAANG job" --category career

  Created: Land a FAANG job (ID: 1)

  Let me ask a few questions to create the right tasks. Ready? [Y/n]: y

  What I already know:
    Current Role: Software Engineer
    Experience Years: 3

  You're a software engineer with 3 years of experience going after FAANG.
  What level are you targeting, and have you started any interview prep?

  > L4/L5, I did some leetcode 6 months ago but I'm rusty

  Got it. What's your biggest weak spot right now — algorithms,
  system design, or behavioral?

  > system design for sure

  go

  Updated your profile with what I learned.

  Generating tasks...

  1. System Design Fundamentals — core patterns and trade-offs (10h) — due 2026-03-01
  2. Design 5 classic systems on paper (8h) — due 2026-03-10
  3. Refresh Leetcode mediums — 30 key problems (15h) — due 2026-03-15
  4. Update resume for L4/L5 FAANG roles (3h) — due 2026-02-20
  5. Schedule 2 mock system design interviews (4h) — due 2026-03-20

  Add these tasks? [Y/n]:
```

Notice: it used your profile (SWE, 3 years) and your answers (system design weakness, L4/L5 target) to generate tasks specific to you.

### 2. Daily Check-in

Compass holds you accountable with daily conversations that reference your actual tasks and progress:

```
$ compass checkin

  You have 1 overdue task and 3 due today. Yesterday you completed
  the resume update. What are you starting with this morning?

  > the leetcode problems

  Good. How many are you aiming for today?

  > 5 medium problems

  That's ambitious for one session. Are you setting a time limit
  or going until all 5 are done?

  > 2 hours max

  Reasonable. Go. Tell me how it went when you're done.

  > done

  Check-in complete.
```

### 3. Interactive Mode

Just run `compass` to open a conversation. Talk naturally, check your tasks, mark things done, or create new goals — all from one place.

**Inline commands** work anywhere in the conversation:

| Command | What it does |
|---------|-------------|
| `/status` | Refresh your dashboard |
| `/goals` | List all goals |
| `/tasks` | List active tasks |
| `/tasks 1` | Tasks for a specific goal |
| `/done 5` | Mark task 5 complete |
| `/new` | Create a new goal |
| `/checkin` | Start daily check-in |
| `/profile` | View your profile |
| `/help` | Show all commands |
| `/quit` | Exit |

### 4. Profile Learning

Compass learns about you from every conversation. When you mention your role, experience, strengths, or weaknesses, it saves that to your profile. Next time, it won't ask again — it'll use what it knows.

Your profile lives at `~/.compass/user_profile.json`. You can also set it up directly:

```bash
compass setup-profile
```

## All Commands

```bash
# The main experience
compass                  # Interactive conversation mode
compass status           # Quick dashboard

# Goals
compass new              # Create goal (conversational)
compass new "Goal name"  # Create with name
compass add-goal "name"  # Alias for new
compass list-goals       # List all goals
compass delete-goal <id> # Delete a goal

# Tasks
compass add-task <goal_id> "description" [--hours 5] [--due 2026-03-01]
compass list-tasks <goal_id>
compass done <task_id>
compass undone <task_id>
compass delete-task <task_id>

# Check-in
compass checkin          # Daily accountability conversation

# Profile
compass setup-profile    # Create/update profile
compass view-profile     # View current profile
```

## Architecture

```
compass/
  main.py       — CLI entry point, interactive mode, all commands
  agent.py      — Claude API integration, conversation management
  database.py   — SQLite operations (goals, tasks, daily logs)
  user_profile.py — User profile management (~/.compass/)
  .env          — Your Anthropic API key (not committed)
  agent.db      — Local SQLite database (not committed)
```

**Data stays local.** The SQLite database and user profile live on your machine. The only external calls are to Anthropic's Claude API for conversation.

## Configuration

The only required configuration is your Anthropic API key in `.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
```

Compass uses Claude Sonnet 4 by default. You can change the model in `agent.py`.

## Contributing

Compass is in active early development. If you have ideas or find bugs, open an issue. See `FUTURE.md` for the roadmap.

## License

MIT
