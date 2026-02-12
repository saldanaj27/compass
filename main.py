import click
import json
from database import Database
from agent import Agent
from user_profile import UserProfile
from datetime import datetime

db = Database()
agent = Agent()
profile = UserProfile()


# ======================================================================
# CLI entry point
# ======================================================================

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Compass — your AI accountability agent."""
    if ctx.invoked_subcommand is None:
        interactive_mode()


# ======================================================================
# Interactive mode — the main experience
# ======================================================================

def show_status_snapshot():
    """Print a quick dashboard of current state."""
    goals = db.get_all_goals()
    today_tasks = db.get_todays_tasks()
    overdue_tasks = db.get_overdue_tasks()
    active_tasks = db.get_all_active_tasks()

    if not goals:
        click.echo("  No goals yet. Type /new to create one.\n")
        return

    click.echo("  Goals:")
    for g in goals:
        goal_tasks = db.get_tasks_for_goal(g['id'])
        done_count = sum(1 for t in goal_tasks if t['status'] == 'done')
        total = len(goal_tasks)
        deadline_str = f" — due {g['deadline']}" if g.get('deadline') else ""
        click.echo(f"    {g['name']} ({done_count}/{total} tasks){deadline_str}")

    lines = []
    if today_tasks:
        lines.append(f"{len(today_tasks)} due today")
    if overdue_tasks:
        lines.append(f"{len(overdue_tasks)} overdue")
    if active_tasks:
        lines.append(f"{len(active_tasks)} active")

    if lines:
        click.echo(f"\n  Tasks: {' | '.join(lines)}")


def handle_inline_command(command: str) -> bool:
    """Handle /commands inside interactive mode. Returns True if handled."""

    parts = command.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if cmd == "/help":
        click.echo("\n  Commands:")
        click.echo("    /status     — refresh dashboard")
        click.echo("    /goals      — list all goals")
        click.echo("    /tasks [id] — list tasks (for a goal, or all active)")
        click.echo("    /done <id>  — mark a task complete")
        click.echo("    /undone <id> — mark a task incomplete")
        click.echo("    /new        — create a new goal")
        click.echo("    /checkin    — start daily check-in")
        click.echo("    /profile    — view your profile")
        click.echo("    /quit       — exit compass")
        click.echo()
        return True

    elif cmd == "/status":
        click.echo()
        show_status_snapshot()
        click.echo()
        return True

    elif cmd == "/goals":
        goals = db.get_all_goals()
        if not goals:
            click.echo("\n  No active goals.\n")
            return True
        click.echo()
        for g in goals:
            goal_tasks = db.get_tasks_for_goal(g['id'])
            done_count = sum(1 for t in goal_tasks if t['status'] == 'done')
            click.echo(f"  [{g['id']}] {g['name']} ({done_count}/{len(goal_tasks)} tasks)")
            if g.get('deadline'):
                click.echo(f"      Deadline: {g['deadline']}")
        click.echo()
        return True

    elif cmd == "/tasks":
        if arg:
            try:
                goal_id = int(arg)
                tasks = db.get_tasks_for_goal(goal_id)
                goal = db.get_goal(goal_id)
                if not tasks:
                    click.echo(f"\n  No tasks for goal {goal_id}.\n")
                    return True
                click.echo(f"\n  Tasks for: {goal['name']}\n")
            except (ValueError, TypeError):
                click.echo(f"\n  Invalid goal ID: {arg}\n")
                return True
        else:
            tasks = db.get_all_active_tasks()
            if not tasks:
                click.echo("\n  No active tasks.\n")
                return True
            click.echo("\n  Active tasks:\n")

        for t in tasks:
            icon = "  done" if t['status'] == 'done' else ""
            overdue = ""
            if t.get('due_date') and t['due_date'] < datetime.now().strftime("%Y-%m-%d") and t['status'] != 'done':
                overdue = " (OVERDUE)"
            due = f" — due {t['due_date']}" if t.get('due_date') else ""
            click.echo(f"  [{t['id']}] {t['description']}{due}{overdue}{icon}")
        click.echo()
        return True

    elif cmd == "/done":
        if not arg:
            click.echo("\n  Usage: /done <task_id>\n")
            return True
        try:
            task_id = int(arg)
            db.complete_task(task_id)
            click.echo(f"\n  Done! Task {task_id} marked complete.\n")
        except (ValueError, TypeError):
            click.echo(f"\n  Invalid task ID: {arg}\n")
        return True

    elif cmd == "/undone":
        if not arg:
            click.echo("\n  Usage: /undone <task_id>\n")
            return True
        try:
            task_id = int(arg)
            db.uncomplete_task(task_id)
            click.echo(f"\n  Task {task_id} marked incomplete.\n")
        except (ValueError, TypeError):
            click.echo(f"\n  Invalid task ID: {arg}\n")
        return True

    elif cmd == "/new":
        click.echo()
        run_new_goal_flow()
        return True

    elif cmd == "/checkin":
        click.echo()
        run_checkin()
        return True

    elif cmd == "/profile":
        if not profile.exists():
            click.echo("\n  No profile yet. I'll learn about you as we talk.\n")
            return True
        summary = profile.get_summary()
        click.echo(f"\n{summary}\n")
        return True

    elif cmd == "/quit":
        return False  # Signal to exit

    else:
        click.echo(f"\n  Unknown command: {cmd}. Type /help for options.\n")
        return True


def interactive_mode():
    """Main interactive conversation mode — the heart of Compass."""

    user_profile = profile.load()
    name = user_profile.get('general', {}).get('name', '')

    # Greeting
    click.echo(f"\n  compass\n")
    greeting = f"Hey{' ' + name if name else ''}."
    click.echo(f"  {greeting} Here's where things stand:\n")

    show_status_snapshot()

    click.echo(f"\n  Talk to me, or type /help for commands.\n")

    # Build system prompt with full context
    goals = db.get_all_goals()
    active_tasks = db.get_all_active_tasks()
    overdue_tasks = db.get_overdue_tasks()
    today_tasks = db.get_todays_tasks()

    system_prompt = agent.build_interactive_system_prompt(
        user_profile, goals, active_tasks, overdue_tasks, today_tasks
    )

    message_history = []

    while True:
        try:
            user_input = click.prompt("  >", prompt_suffix=" ")
        except (EOFError, KeyboardInterrupt):
            click.echo("\n")
            break

        stripped = user_input.strip()

        if stripped.lower() in ['quit', 'exit', 'q']:
            click.echo("\n  See you.\n")
            break

        # Handle /commands
        if stripped.startswith('/'):
            result = handle_inline_command(stripped)
            if result is False:  # /quit
                click.echo("\n  See you.\n")
                break
            continue

        # Send to agent for conversation
        response = agent.conversation_turn(message_history, stripped, system_prompt=system_prompt)
        message_history.append({"role": "assistant", "content": response})

        click.echo(f"\n  {response}\n")


# ======================================================================
# Status command
# ======================================================================

@cli.command()
def status():
    """Quick dashboard of goals, tasks, and what's due."""
    click.echo(f"\n  compass status — {datetime.now().strftime('%A, %B %d')}\n")
    show_status_snapshot()

    overdue = db.get_overdue_tasks()
    today = db.get_todays_tasks()

    if overdue:
        click.echo(f"\n  Overdue:")
        for t in overdue:
            click.echo(f"    [{t['id']}] {t['description']} — due {t['due_date']}")

    if today:
        click.echo(f"\n  Due today:")
        for t in today:
            click.echo(f"    [{t['id']}] {t['description']}")

    click.echo()


# ======================================================================
# Goal management
# ======================================================================

@cli.command('new')
@click.argument('name', required=False)
@click.option('--description', '-d', default="")
@click.option('--deadline', default=None, help="Format: YYYY-MM-DD")
@click.option('--category', '-c', default="general",
              help="Goal category (career, health, finance, learning, general)")
def new_goal(name, description, deadline, category):
    """Create a new goal with conversational task breakdown."""
    run_new_goal_flow(name, description, deadline, category)


# Keep old command name as alias
@cli.command('add-goal')
@click.argument('name')
@click.option('--description', '-d', default="")
@click.option('--deadline', default=None, help="Format: YYYY-MM-DD")
@click.option('--category', '-c', default="general")
def add_goal(name, description, deadline, category):
    """Create a new goal (alias for 'new')."""
    run_new_goal_flow(name, description, deadline, category)


def run_new_goal_flow(name=None, description="", deadline=None, category="general"):
    """Conversational goal creation flow. Used by both /new command and inline."""

    user_profile = profile.load()

    # If no name provided, ask for it
    if not name:
        name = click.prompt("  What's the goal?", type=str)

    # Check for profile, offer quick setup on first use
    if not profile.exists():
        click.echo("\n  First time? A quick profile helps me personalize your tasks.\n")
        if click.confirm("  Set up profile?", default=True):
            setup_profile_interactive()
            user_profile = profile.load()

    goal_id = db.add_goal(name, description, deadline, category)
    click.echo(f"\n  Created: {name} (ID: {goal_id})")

    # Start discovery conversation
    if not click.confirm("\n  Let me ask a few questions to create the right tasks. Ready?", default=True):
        click.echo(f"  Goal saved. Add tasks later with: compass add-task {goal_id} <description>\n")
        return

    # Show what we already know
    if user_profile and category in user_profile and user_profile[category]:
        known_items = {k: v for k, v in user_profile[category].items() if v}
        if known_items:
            click.echo("\n  What I already know:")
            for key, value in known_items.items():
                click.echo(f"    {key.replace('_', ' ').title()}: {value}")
            click.echo()

    # Discovery conversation
    greeting = agent.goal_discovery_greeting(name, user_profile, category)
    click.echo(f"  {greeting}\n")

    message_history = [{"role": "assistant", "content": greeting}]

    click.echo("  (Type 'go' when ready to generate tasks)\n")

    for _ in range(8):
        user_input = click.prompt("  >", prompt_suffix=" ")

        if user_input.strip().lower() in ['go', 'done', 'generate']:
            break

        response = agent.conversation_turn(message_history, user_input)
        message_history.append({"role": "assistant", "content": response})
        click.echo(f"\n  {response}\n")

    # Extract and save learnings to profile
    profile_updates = agent.extract_profile_updates(message_history, category)
    if profile_updates:
        profile.update_category(category, profile_updates)
        click.echo("  Updated your profile with what I learned.\n")

    # Store goal context
    conversation_summary = "\n".join([f"{m['role']}: {m['content']}" for m in message_history])
    db.update_goal_context(goal_id, json.dumps({'conversation': conversation_summary}))

    # Generate tasks
    click.echo("  Generating tasks...\n")
    tasks = agent.generate_tasks_from_context(
        name, description, conversation_summary, user_profile, deadline
    )

    if not tasks:
        click.echo("  Couldn't generate tasks. Add them manually with /tasks.\n")
        return

    # Show tasks
    for i, task in enumerate(tasks, 1):
        line = f"  {i}. {task['description']}"
        if task.get('estimated_hours'):
            line += f" ({task['estimated_hours']}h)"
        if task.get('due_date'):
            line += f" — due {task['due_date']}"
        click.echo(line)
    click.echo()

    # Confirm loop
    while True:
        if click.confirm("  Add these tasks?", default=True):
            for task in tasks:
                db.add_task(goal_id, task['description'],
                           task.get('estimated_hours'), task.get('due_date'))
            click.echo(f"\n  Added {len(tasks)} tasks to \"{name}\".\n")
            break
        else:
            click.echo("\n  1. Regenerate (tell me what to change)")
            click.echo("  2. Save goal without tasks")
            click.echo("  3. Delete goal")
            click.echo("  4. Talk it through")

            choice = click.prompt("\n  Choice", type=click.Choice(['1', '2', '3', '4']))

            if choice == '1':
                feedback = click.prompt("  What should be different?", type=str)
                context_with_feedback = conversation_summary + f"\n\nUser feedback on tasks: {feedback}"
                click.echo("\n  Regenerating...\n")
                tasks = agent.generate_tasks_from_context(
                    name, description, context_with_feedback, user_profile, deadline
                )
                for i, task in enumerate(tasks, 1):
                    line = f"  {i}. {task['description']}"
                    if task.get('estimated_hours'):
                        line += f" ({task['estimated_hours']}h)"
                    if task.get('due_date'):
                        line += f" — due {task['due_date']}"
                    click.echo(line)
                click.echo()

            elif choice == '2':
                click.echo(f"\n  Goal saved. Add tasks with: compass add-task {goal_id} <desc>\n")
                break

            elif choice == '3':
                db.delete_goal(goal_id)
                click.echo("\n  Goal deleted.\n")
                break

            elif choice == '4':
                click.echo("\n  What's on your mind?\n")
                chat_history = []
                while True:
                    user_input = click.prompt("  >", prompt_suffix=" ")
                    if user_input.strip().lower() in ['done', 'exit', 'back']:
                        click.echo(f"\n  Goal \"{name}\" is saved. Add tasks when ready.\n")
                        break
                    response = agent.conversation_turn(chat_history, user_input)
                    chat_history.append({"role": "assistant", "content": response})
                    click.echo(f"\n  {response}\n")
                break


def setup_profile_interactive():
    """Quick interactive profile setup."""
    click.echo()
    name = click.prompt("  Name", default="", type=str)
    role = click.prompt("  Current role", default="", type=str)
    hours = click.prompt("  Hours/day available for goals", default=2, type=int)

    profile.save({
        "general": {"name": name, "availability_hours_per_day": hours},
        "career": {"current_role": role}
    })
    click.echo("\n  Profile created.\n")


# ======================================================================
# Check-in
# ======================================================================

@cli.command()
def checkin():
    """Daily check-in conversation."""
    run_checkin()


def run_checkin():
    """Check-in flow. Used by both command and /checkin."""

    goals = db.get_all_goals()
    yesterday_tasks = db.get_yesterdays_completed_tasks()
    today_tasks = db.get_todays_tasks()
    overdue_tasks = db.get_overdue_tasks()

    context = {
        'goals': goals,
        'yesterday_tasks': yesterday_tasks,
        'today_tasks': today_tasks,
        'overdue_tasks': overdue_tasks
    }

    greeting = agent.daily_checkin_greeting(context)
    click.echo(f"\n  {greeting}\n")

    message_history = [{"role": "assistant", "content": greeting}]

    click.echo("  (Type 'done' to end check-in)\n")

    while True:
        try:
            user_input = click.prompt("  >", prompt_suffix=" ")
        except (EOFError, KeyboardInterrupt):
            click.echo("\n")
            break

        if user_input.strip().lower() in ['done', 'exit', 'bye', 'quit']:
            click.echo("\n  Check-in complete.\n")
            break

        response = agent.conversation_turn(message_history, user_input, context=context)
        message_history.append({"role": "assistant", "content": response})
        click.echo(f"\n  {response}\n")


# ======================================================================
# Task management (subcommands for power users)
# ======================================================================

@cli.command('add-task')
@click.argument('goal_id', type=int)
@click.argument('description')
@click.option('--hours', '-h', type=float, help="Estimated hours")
@click.option('--due', help="Due date (YYYY-MM-DD)")
def add_task(goal_id, description, hours, due):
    """Add a task to a goal."""
    task_id = db.add_task(goal_id, description, hours, due)
    click.echo(f"  Added: {description} (ID: {task_id})")


@cli.command('list-goals')
def list_goals():
    """List all active goals."""
    goals = db.get_all_goals()
    if not goals:
        click.echo("  No active goals.")
        return
    click.echo()
    for g in goals:
        goal_tasks = db.get_tasks_for_goal(g['id'])
        done_count = sum(1 for t in goal_tasks if t['status'] == 'done')
        click.echo(f"  [{g['id']}] {g['name']} ({done_count}/{len(goal_tasks)} tasks)")
        if g.get('deadline'):
            click.echo(f"      Deadline: {g['deadline']}")
    click.echo()


@cli.command('list-tasks')
@click.argument('goal_id', type=int)
def list_tasks(goal_id):
    """List tasks for a goal."""
    tasks = db.get_tasks_for_goal(goal_id)
    if not tasks:
        click.echo(f"  No tasks for goal {goal_id}")
        return

    goal = db.get_goal(goal_id)
    click.echo(f"\n  {goal['name']}:\n")
    for t in tasks:
        icon = "x" if t['status'] == 'done' else " "
        line = f"  [{icon}] {t['id']}: {t['description']}"
        if t.get('estimated_hours'):
            line += f" ({t['estimated_hours']}h)"
        if t.get('due_date'):
            line += f" — due {t['due_date']}"
        click.echo(line)
    click.echo()


@cli.command()
@click.argument('task_id', type=int)
def done(task_id):
    """Mark a task as complete."""
    db.complete_task(task_id)
    click.echo(f"  Done! Task {task_id} complete.")


@cli.command()
@click.argument('task_id', type=int)
def undone(task_id):
    """Mark a task as incomplete."""
    db.uncomplete_task(task_id)
    click.echo(f"  Task {task_id} marked incomplete.")


@cli.command('delete-task')
@click.argument('task_id', type=int)
def delete_task(task_id):
    """Delete a task."""
    db.delete_task(task_id)
    click.echo(f"  Deleted task {task_id}.")


@cli.command('delete-goal')
@click.argument('goal_id', type=int)
def delete_goal(goal_id):
    """Delete a goal and all its tasks."""
    if click.confirm(f"  Delete goal {goal_id} and all its tasks?"):
        db.delete_goal(goal_id)
        click.echo(f"  Deleted goal {goal_id}.")


# ======================================================================
# Profile management
# ======================================================================

@cli.command('setup-profile')
def setup_profile_cmd():
    """Create or update your user profile."""
    existing = profile.load()

    click.echo("\n  Profile Setup\n")

    name = click.prompt("  Name",
                        default=existing.get('general', {}).get('name', ''))
    hours = click.prompt("  Hours/day for goals",
                         default=existing.get('general', {}).get('availability_hours_per_day', 2),
                         type=int)
    role = click.prompt("  Current role",
                        default=existing.get('career', {}).get('current_role', ''))
    years = click.prompt("  Years of experience",
                         default=existing.get('career', {}).get('experience_years', 0),
                         type=int)

    strengths_default = ', '.join(existing.get('career', {}).get('strengths', []))
    strengths = click.prompt("  Strengths (comma-separated)", default=strengths_default)

    weaknesses_default = ', '.join(existing.get('career', {}).get('weaknesses', []))
    weaknesses = click.prompt("  Weaknesses (comma-separated)", default=weaknesses_default)

    profile_data = {
        "general": {"name": name, "availability_hours_per_day": hours},
        "career": {
            "current_role": role,
            "experience_years": years,
            "strengths": [s.strip() for s in strengths.split(',') if s.strip()],
            "weaknesses": [w.strip() for w in weaknesses.split(',') if w.strip()]
        },
        "learning": existing.get('learning', {}),
        "health": existing.get('health', {}),
        "finance": existing.get('finance', {})
    }

    profile.save(profile_data)
    click.echo("\n  Profile saved.\n")


@cli.command('view-profile')
def view_profile():
    """View your profile."""
    if not profile.exists():
        click.echo("\n  No profile yet. Run 'compass setup-profile' or just start a conversation.\n")
        return
    click.echo(profile.get_summary())
    click.echo()


if __name__ == '__main__':
    cli()
