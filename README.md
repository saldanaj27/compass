# Compass

An AI agent that keeps you accountable to your goals.

Compass isn't a task manager. It's a personal AI agent that learns about you, understands your specific situation, and holds you accountable through direct, honest conversations.

You talk to it. It remembers. It pushes back when you're slacking. It knows your goals, your deadlines, and your weak spots — because you told it, and it didn't forget.

## What It Looks Like

```
$ compass

  compass

  Hey Alex. Here's where things stand:

  Goals:
    Build ML Portfolio (3/8 tasks) — due 2026-05-01
    Learn Transformers from Scratch (1/6 tasks)

  Tasks: 2 due today | 1 overdue | 10 active

  Talk to me, or type /help for commands.

  > I haven't started the transformer implementation yet

  That's been on your list for 10 days. You said you understood
  the attention mechanism conceptually but hadn't coded it.
  What's the actual blocker — is it the math or the PyTorch setup?

  > the math honestly, I keep re-reading the paper and getting lost

  Stop re-reading. Open a notebook and implement scaled dot-product
  attention in 20 lines of NumPy first. No PyTorch, no full model.
  Just Q, K, V matrices and the attention formula. Can you do that tonight?

  > yeah that sounds way more manageable

  Good. Once that clicks, the rest is just stacking layers.
  What time are you sitting down to do it?

  > after dinner, around 8

  I'll ask you about it tomorrow. Go make it work.

  > /done 12

  Done! Task 12 marked complete.

  > quit

  See you.
```

## Why Compass

**It remembers you.** Your profile builds automatically from conversations. Tell it you're struggling with attention mechanisms once — it won't ask again, but it will hold you to working through it.

**It's direct.** No "great job!" for doing the bare minimum. Compass asks what's blocking you, calls out avoidance, and pushes you to be specific about commitments.

**It's personal.** When you add a goal, Compass asks about YOUR situation before generating tasks. Not generic "study ML for 40 hours" — specific tasks based on your background, gaps, and timeline.

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
$ compass new "Build an ML portfolio" --category learning

  Created: Build an ML portfolio (ID: 1)

  Let me ask a few questions to create the right tasks. Ready? [Y/n]: y

  What I already know:
    Current Role: Software Engineer
    Experience Years: 3

  You're a software engineer looking to build an ML portfolio.
  What's your current ML experience — have you trained models before,
  or are you starting from fundamentals?

  > I've done some tutorials and a Kaggle competition but nothing production-level

  Got it. Are you building this portfolio to transition into an ML role,
  or to add ML skills to your current work?

  > transition into an ML engineer role

  go

  Updated your profile with what I learned.

  Generating tasks...

  1. Implement a transformer from scratch in PyTorch (12h) — due 2026-03-01
  2. Build end-to-end NLP project with dataset, training, eval (15h) — due 2026-03-15
  3. Deploy a model with FastAPI + write a technical blog post (8h) — due 2026-03-22
  4. Contribute to an open-source ML library (6h) — due 2026-04-01
  5. Build a computer vision project with real-world dataset (10h) — due 2026-04-15

  Add these tasks? [Y/n]:
```

Notice: it used your profile (SWE, 3 years) and your answers (tutorial-level ML, wants to transition) to generate tasks specific to you.

### 2. Daily Check-in

Compass holds you accountable with daily conversations that reference your actual tasks and progress:

```
$ compass checkin

  You have 1 overdue task and 2 due today. Yesterday you finished
  the data preprocessing pipeline. What are you working on today?

  > I need to start training the model but I'm not sure about hyperparameters

  You've been researching hyperparameters for three days. Pick reasonable
  defaults, train a baseline, and iterate from there. What learning rate
  are you starting with?

  > fine, 1e-4 with AdamW

  Good call. Set a 2-hour training run and evaluate. Don't tune anything
  until you have baseline metrics. When are you starting?

  > right now

  Go. Come back with your loss curves.

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
