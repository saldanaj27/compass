import click
import json
from database import Database
from agent import Agent
from profile import UserProfile
from datetime import datetime

db = Database()
agent = Agent()
profile = UserProfile()

@click.group()
def cli():
    """Personal Task Agent - Your AI productivity manager"""
    pass

@cli.command()
@click.argument('name')
@click.option('--description', '-d', default="")
@click.option('--deadline', default=None, help="Format: YYYY-MM-DD")
@click.option('--category', '-c', default="general", help="Goal category (career, health, finance, learning, general)")
def add_goal(name, description, deadline, category):
    """Add a new goal with conversational task breakdown"""

    # Load user profile
    user_profile = profile.load()

    # Check if profile exists, offer to create one if not
    if not profile.exists():
        click.echo("\n👋 First time? Let me create a quick profile to personalize your experience.\n")
        if click.confirm("Create profile now? (Recommended)", default=True):
            setup_profile_interactive()
            user_profile = profile.load()
        else:
            click.echo("Skipping profile setup. You can run 'compass setup-profile' later.\n")

    # Add goal to database (without context yet)
    goal_id = db.add_goal(name, description, deadline, category)
    click.echo(f"\n✓ Created goal: {name} (ID: {goal_id})")

    # Start discovery conversation
    if not click.confirm("\nLet me understand your situation to create personalized tasks. Ready?", default=True):
        click.echo("Goal created. Run 'compass goal-breakdown <goal_id>' later to add tasks.")
        return

    click.echo("\n🤖 Starting discovery conversation...\n")

    # Show what agent already knows from profile
    if user_profile and category in user_profile and user_profile[category]:
        click.echo("📋 What I already know about you:")
        for key, value in user_profile[category].items():
            if value:  # Only show non-empty values
                # Make it human-readable
                key_readable = key.replace('_', ' ').title()
                click.echo(f"  - {key_readable}: {value}")
        click.echo()

    # Get opening question from agent
    greeting = agent.goal_discovery_greeting(name, user_profile, category)
    click.echo(f"🤖 {greeting}\n")

    # Conversation loop to gather context
    message_history = [{"role": "assistant", "content": greeting}]
    context_data = {}

    click.echo("(Type 'done' when ready to generate tasks)\n")

    turn_count = 0
    max_turns = 5  # Limit discovery to 5 exchanges

    while turn_count < max_turns:
        user_input = click.prompt("You", type=str)

        if user_input.lower() == 'done':
            break

        # Get agent response
        response = agent.conversation_turn(message_history, user_input)
        message_history.append({"role": "assistant", "content": response})

        click.echo(f"\n🤖 {response}\n")
        turn_count += 1

    # Extract context from conversation
    conversation_summary = "\n".join([f"{msg['role']}: {msg['content']}" for msg in message_history])
    context_data['conversation'] = conversation_summary

    # Store context in database
    db.update_goal_context(goal_id, json.dumps(context_data))

    # Extract learnings from conversation and update user profile
    click.echo("\n💾 Updating your profile with what I learned...\n")
    profile_updates = agent.extract_profile_updates(message_history, category)

    if profile_updates:
        # Update the specific category in profile
        profile.update_category(category, profile_updates)

        # Show what was learned
        click.echo("✓ Learned and saved to your profile:")
        for key, value in profile_updates.items():
            if value:  # Only show non-empty values
                click.echo(f"  - {key}: {value}")
        click.echo()
    else:
        click.echo("(No new profile information to save)")

    # Generate tasks from context
    click.echo("\n💭 Generating personalized tasks based on your situation...\n")

    tasks = agent.generate_tasks_from_context(
        name,
        description,
        json.dumps(context_data),
        user_profile,
        deadline
    )

    if not tasks:
        click.echo("⚠️  Couldn't generate tasks automatically. You can add them manually with 'add-task'.")
        return

    # Display generated tasks
    click.echo("📝 Here are your personalized tasks:\n")
    for i, task in enumerate(tasks, 1):
        click.echo(f"{i}. {task['description']}")
        if task.get('estimated_hours'):
            click.echo(f"   Est: {task['estimated_hours']}h")
        if task.get('due_date'):
            click.echo(f"   Due: {task['due_date']}")
        click.echo()

    # Ask to confirm adding tasks
    while True:
        if click.confirm("\nAdd these tasks to your goal?", default=True):
            for task in tasks:
                db.add_task(
                    goal_id,
                    task['description'],
                    task.get('estimated_hours'),
                    task.get('due_date')
                )
            click.echo(f"\n✅ Added {len(tasks)} tasks to '{name}'!")
            break
        else:
            # User said no - find out why and offer options
            click.echo("\n🤔 Got it. What would you like to do?\n")
            click.echo("1. Regenerate tasks (I'll ask more questions)")
            click.echo("2. Keep goal, add tasks manually later")
            click.echo("3. Delete goal and start over")
            click.echo("4. Just talk about it")

            choice = click.prompt("\nYour choice", type=click.Choice(['1', '2', '3', '4']))

            if choice == '1':
                click.echo("\n💭 Let me ask a few more questions...\n")

                # Ask what was wrong with the tasks
                feedback = click.prompt("What didn't work about those tasks?", type=str)

                # Add feedback to context
                context_data['feedback'] = feedback

                # Regenerate with feedback
                click.echo("\n💭 Regenerating with your feedback...\n")
                tasks = agent.generate_tasks_from_context(
                    name,
                    description,
                    json.dumps(context_data),
                    user_profile,
                    deadline
                )

                # Display new tasks
                click.echo("📝 Here are revised tasks:\n")
                for i, task in enumerate(tasks, 1):
                    click.echo(f"{i}. {task['description']}")
                    if task.get('estimated_hours'):
                        click.echo(f"   Est: {task['estimated_hours']}h")
                    if task.get('due_date'):
                        click.echo(f"   Due: {task['due_date']}")
                    click.echo()
                # Loop back to ask again

            elif choice == '2':
                click.echo(f"\n✓ Goal '{name}' saved without tasks.")
                click.echo(f"   Add tasks later with: compass add-task {goal_id} <description>")
                break

            elif choice == '3':
                db.delete_goal(goal_id)
                click.echo(f"\n✓ Goal deleted. Run 'add-goal' again when ready.")
                break

            elif choice == '4':
                click.echo("\n🤖 I'm listening. What's on your mind?\n")

                # Start a conversation about the goal
                message_history = []

                while True:
                    user_input = click.prompt("You", type=str)

                    if user_input.lower() in ['done', 'exit', 'nevermind']:
                        click.echo("\n✓ Alright. Your goal is saved. Add tasks when ready.")
                        break

                    # Agent responds
                    response = agent.conversation_turn(message_history, user_input)
                    message_history.append({"role": "assistant", "content": response})
                    click.echo(f"\n🤖 {response}\n")

                break


def setup_profile_interactive():
    """Interactive profile setup (helper function)"""
    click.echo("Quick profile setup:\n")

    name = click.prompt("Your name", default="", type=str)
    current_role = click.prompt("Current role/occupation", default="", type=str)
    hours_per_day = click.prompt("Hours available per day for goals", default=2, type=int)

    profile_data = {
        "general": {
            "name": name,
            "availability_hours_per_day": hours_per_day
        },
        "career": {
            "current_role": current_role
        }
    }

    profile.save(profile_data)
    click.echo("\n✓ Profile created! You can update it anytime with 'compass setup-profile'\n")

@cli.command()
def setup_profile():
    """Create or update your user profile"""
    click.echo("\n📝 Profile Setup\n")

    existing_profile = profile.load()

    if existing_profile:
        click.echo("You already have a profile. Let's update it.\n")

    # General info
    click.echo("GENERAL INFO:")
    name = click.prompt("Name", default=existing_profile.get('general', {}).get('name', ''), type=str)
    hours_per_day = click.prompt("Hours/day available for goals",
                                 default=existing_profile.get('general', {}).get('availability_hours_per_day', 2),
                                 type=int)

    # Career info
    click.echo("\nCAREER:")
    current_role = click.prompt("Current role",
                               default=existing_profile.get('career', {}).get('current_role', ''),
                               type=str)
    experience_years = click.prompt("Years of experience",
                                   default=existing_profile.get('career', {}).get('experience_years', 0),
                                   type=int)
    strengths = click.prompt("Strengths (comma-separated)",
                            default=', '.join(existing_profile.get('career', {}).get('strengths', [])),
                            type=str)
    weaknesses = click.prompt("Weaknesses (comma-separated)",
                             default=', '.join(existing_profile.get('career', {}).get('weaknesses', [])),
                             type=str)

    # Save profile
    profile_data = {
        "general": {
            "name": name,
            "availability_hours_per_day": hours_per_day
        },
        "career": {
            "current_role": current_role,
            "experience_years": experience_years,
            "strengths": [s.strip() for s in strengths.split(',')] if strengths else [],
            "weaknesses": [w.strip() for w in weaknesses.split(',')] if weaknesses else []
        },
        "learning": existing_profile.get('learning', {}),
        "health": existing_profile.get('health', {}),
        "finance": existing_profile.get('finance', {})
    }

    profile.save(profile_data)
    click.echo("\n✅ Profile saved!\n")

@cli.command()
def view_profile():
    """View your current user profile"""
    if not profile.exists():
        click.echo("\n⚠️  No profile found. Run 'compass setup-profile' to create one.\n")
        return

    summary = profile.get_summary()
    click.echo(f"\n📋 Your Profile:\n{summary}\n")

@cli.command()
def list_goals():
    """List all active goals"""
    goals = db.get_all_goals()
    
    if not goals:
        click.echo("No active goals. Add one with: add-goal <name>")
        return
    
    click.echo("\n📋 Your Goals:\n")
    for goal in goals:
        click.echo(f"ID {goal['id']}: {goal['name']}")
        if goal['deadline']:
            click.echo(f"   Deadline: {goal['deadline']}")
        if goal['description']:
            click.echo(f"   {goal['description']}")
        click.echo()

@cli.command()
@click.argument('goal_id', type=int)
@click.argument('description')
@click.option('--hours', '-h', type=float, help="Estimated hours")
@click.option('--due', help="Due date (YYYY-MM-DD)")
def add_task(goal_id, description, hours, due):
    """Add a task to a goal"""
    task_id = db.add_task(goal_id, description, hours, due)
    click.echo(f"✓ Added task: {description} (ID: {task_id})")

@cli.command()
@click.argument('goal_id', type=int)
def list_tasks(goal_id):
    """List tasks for a goal"""
    tasks = db.get_tasks_for_goal(goal_id)
    
    if not tasks:
        click.echo(f"No tasks for goal {goal_id}")
        return
    
    click.echo(f"\n📝 Tasks for Goal {goal_id}:\n")
    for task in tasks:
        status_icon = "✓" if task['status'] == 'done' else "○"
        click.echo(f"{status_icon} ID {task['id']}: {task['description']}")
        if task['estimated_hours']:
            click.echo(f"   Est: {task['estimated_hours']}h")
        if task['due_date']:
            click.echo(f"   Due: {task['due_date']}")
        click.echo()

@cli.command()
def checkin():
    """Daily check-in conversation with agent"""

    # Gather context
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

    # Start conversation with greeting
    greeting = agent.daily_checkin_greeting(context)
    click.echo(f"\n🤖 {greeting}\n")

    # Conversation loop
    message_history = [{"role": "assistant", "content": greeting}]

    click.echo("(Type 'done', 'exit', or 'bye' to end conversation)\n")

    while True:
        user_input = click.prompt("You", type=str)

        # Check for exit keywords
        if user_input.lower() in ['done', 'exit', 'bye', 'quit']:
            click.echo("\n✓ Check-in complete!\n")
            break

        # Get agent response
        response = agent.conversation_turn(message_history, user_input, context)

        # Add response to history for next turn
        message_history.append({"role": "assistant", "content": response})

        # Display response
        click.echo(f"\n🤖 {response}\n")

    # Optional: Ask if user wants to log progress for any specific task
    if click.confirm("\nWant to log progress on a specific task?", default=False):
        all_tasks = db.get_all_active_tasks()
        if not all_tasks:
            click.echo("No active tasks to log progress for.")
            return

        click.echo("\nActive tasks:")
        for i, task in enumerate(all_tasks, 1):
            click.echo(f"{i}. {task['description']}")

        task_num = click.prompt("Which task? (number)", type=int)
        if 1 <= task_num <= len(all_tasks):
            task = all_tasks[task_num - 1]
            hours = click.prompt("Hours spent", type=float)
            notes = click.prompt("Notes (optional)", default="", type=str)

            db.log_progress(task['id'], hours, notes)
            click.echo(f"\n✓ Logged {hours} hours on: {task['description']}")

@cli.command()
@click.argument('task_id', type=int)
def delete_task(task_id):
    """Delete a task"""
    if click.confirm(f"Delete task {task_id}?"):
        db.delete_task(task_id)
        click.echo(f"✓ Deleted task {task_id}")

@cli.command()
@click.argument('goal_id', type=int)
def delete_goal(goal_id):
    """Delete a goal and all its tasks"""
    if click.confirm(f"Delete goal {goal_id} and ALL its tasks?"):
        db.delete_goal(goal_id)
        click.echo(f"✓ Deleted goal {goal_id}")

@cli.command()
@click.argument('task_id', type=int)
def done(task_id):
    """Mark a task as complete"""
    db.complete_task(task_id)
    click.echo(f"✓ Completed task {task_id}")

@cli.command()
@click.argument('task_id', type=int)
def undone(task_id):
    """Mark a task as incomplete"""
    db.uncomplete_task(task_id)
    click.echo(f"○ Marked task {task_id} as incomplete")

if __name__ == '__main__':
    cli()