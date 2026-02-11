import click
from database import Database
from agent import Agent
from datetime import datetime

db = Database()
agent = Agent()

@click.group()
def cli():
    """Personal Task Agent - Your AI productivity manager"""
    pass

@cli.command()
@click.argument('name')
@click.option('--description', '-d', default="")
@click.option('--deadline', default=None, help="Format: YYYY-MM-DD")
def add_goal(name, description, deadline):
    """Add a new goal"""
    goal_id = db.add_goal(name, description, deadline)
    click.echo(f"\n✓ Added goal: {name} (ID: {goal_id})")
    
    # Ask if they want AI to break it down
    if click.confirm("\nWould you like me to break this goal into tasks?"):
        click.echo("\nThinking...")
        breakdown = agent.break_down_goal(name, description, deadline)
        click.echo(f"\n{breakdown}")
        
        if click.confirm("\nWould you like to add these tasks?"):
            click.echo("(Manual task addition coming in next version)")

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
    """Daily check-in with your agent"""
    click.echo("\n🤖 Daily Check-in\n")
    
    # Get context
    goals = db.get_all_goals()
    context = {
        'goals': [g['name'] for g in goals],
        'yesterday_tasks': [],  # TODO: Get from DB
        'today_tasks': []  # TODO: Get from DB
    }
    
    # Agent greeting
    greeting = agent.daily_checkin(context)
    click.echo(greeting)
    click.echo()
    
    # Simple progress logging for now
    click.echo("What did you work on today? (or 'skip')")
    notes = click.prompt("", default="skip")
    
    if notes != "skip":
        hours = click.prompt("How many hours?", type=float)
        db.log_progress(task_id=None, hours_spent=hours, notes=notes)
        click.echo("\n✓ Logged progress!")

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