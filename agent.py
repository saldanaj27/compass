import os
import re
import json
from datetime import datetime
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

class Agent:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-sonnet-4-20250514"

    def _clean_markdown(self, text: str) -> str:
        """Remove markdown formatting for CLI display"""
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)
        text = re.sub(r'_(.+?)_', r'\1', text)
        return text

    def _today(self) -> str:
        return datetime.now().strftime("%Y-%m-%d")

    # ------------------------------------------------------------------
    # Interactive mode
    # ------------------------------------------------------------------

    def build_interactive_system_prompt(self, user_profile: dict, goals: list,
                                         active_tasks: list, overdue_tasks: list,
                                         today_tasks: list) -> str:
        """Build a rich system prompt for interactive conversation mode.

        Gives the agent full context so it can have an informed conversation.
        """
        name = user_profile.get('general', {}).get('name', '')

        prompt = f"""You are Compass, a personal AI accountability agent. Today is {self._today()}.
{f'You are talking to {name}.' if name else ''}

Your personality: direct, firm, conversational. You don't waste words. You ask pointed questions.
You hold the user accountable to what they committed to — respectfully but firmly.
When the user is stuck, help them think through it. When they're avoiding something, name it.
Keep responses to 2-4 sentences unless more detail is needed.

Do NOT use markdown formatting (no bold, italics, bullet points). Write in plain conversational text.
"""

        # Goals and tasks context
        if goals:
            prompt += "\nACTIVE GOALS:\n"
            for g in goals:
                prompt += f"- \"{g['name']}\" (ID {g['id']})"
                if g.get('deadline'):
                    prompt += f" — deadline {g['deadline']}"
                prompt += "\n"

        if overdue_tasks:
            prompt += f"\nOVERDUE TASKS ({len(overdue_tasks)}):\n"
            for t in overdue_tasks:
                prompt += f"- ID {t['id']}: \"{t['description']}\" (due {t['due_date']})\n"

        if today_tasks:
            prompt += f"\nDUE TODAY ({len(today_tasks)}):\n"
            for t in today_tasks:
                prompt += f"- ID {t['id']}: \"{t['description']}\"\n"

        if active_tasks:
            prompt += f"\nALL ACTIVE TASKS ({len(active_tasks)}):\n"
            for t in active_tasks:
                status = "overdue" if t.get('due_date') and t['due_date'] < self._today() else "pending"
                prompt += f"- ID {t['id']}: \"{t['description']}\" ({status})\n"

        # Profile context
        if user_profile:
            prompt += "\nUSER PROFILE:\n"
            for category, data in user_profile.items():
                if data and any(v for v in data.values()):
                    for key, value in data.items():
                        if value:
                            prompt += f"- {key}: {value}\n"

        prompt += """
IMPORTANT BEHAVIORS:
- When the user says they finished something, acknowledge it and ask what's next.
- When the user wants to add a new goal, tell them to use: /new (it starts a guided flow).
- When the user asks about their tasks or goals, reference the actual data above.
- When the user seems stuck or avoidant, ask what's specifically blocking them.
- If the user asks you to mark something done, tell them to use /done <task_id>.
- Keep the conversation moving forward. Always end with a question or next step.
"""
        return prompt

    def conversation_turn(self, message_history: list, user_message: str,
                          system_prompt: str = None, context: dict = None) -> str:
        """Handle one turn of a multi-turn conversation.

        Args:
            message_history: List of {"role": "user"|"assistant", "content": "..."}
            user_message: Latest message from user
            system_prompt: Optional system prompt (used by interactive mode)
            context: Optional context dict (used by checkin mode, builds its own system prompt)
        """

        if not system_prompt and context:
            system_prompt = """You are a direct, firm accountability agent. Your job is to keep the user on track with their goals.

Be conversational but don't waste words. Ask pointed questions about progress and blockers.
If user committed to something, hold them to it (respectfully but firmly).
If user is avoiding work, ask what's really getting in the way.

Keep responses to 2-3 sentences. Be helpful but direct."""

            if context.get('goals'):
                system_prompt += f"\n\nCurrent context:\n"
                system_prompt += f"- Active goals: {', '.join([g['name'] for g in context['goals']])}\n"
            if context.get('overdue_tasks'):
                system_prompt += f"- Overdue tasks: {len(context['overdue_tasks'])} tasks are past due\n"
            if context.get('today_tasks'):
                system_prompt += f"- Today's tasks: {len(context['today_tasks'])} tasks due today\n"

        elif not system_prompt:
            system_prompt = "You are a direct, helpful personal productivity agent. Keep responses concise."

        message_history.append({"role": "user", "content": user_message})

        message = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            system=system_prompt,
            messages=message_history
        )

        response = message.content[0].text
        return self._clean_markdown(response)

    # ------------------------------------------------------------------
    # Daily check-in
    # ------------------------------------------------------------------

    def daily_checkin_greeting(self, context: dict) -> str:
        """Generate opening greeting for daily check-in."""

        prompt = f"""You are starting a daily check-in conversation. Be direct and firm.
Today's date is {self._today()}.

Context:
- Active goals: {[g['name'] for g in context.get('goals', [])]}
- Yesterday's completed tasks: {len(context.get('yesterday_tasks', []))} tasks
- Today's planned tasks: {len(context.get('today_tasks', []))} tasks
- Overdue tasks: {len(context.get('overdue_tasks', []))} tasks

Start with a brief, direct greeting (2-3 sentences).
Reference specific context (overdue tasks, yesterday's work, etc.).
Ask what they're working on today.
Do NOT use markdown formatting."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        return self._clean_markdown(message.content[0].text)

    # ------------------------------------------------------------------
    # Goal discovery and task generation
    # ------------------------------------------------------------------

    def goal_discovery_greeting(self, goal_name: str, user_profile: dict,
                                category: str = "general") -> str:
        """Start discovery conversation for a new goal."""

        profile_context = ""
        if user_profile and category in user_profile:
            for key, value in user_profile[category].items():
                if value:
                    profile_context += f"- {key}: {value}\n"

        prompt = f"""You are helping a user set up a new goal: "{goal_name}"
Today's date: {self._today()}
Category: {category}
{"I already know from their profile:" + chr(10) + profile_context if profile_context else "No existing profile data for this category."}

Ask 1-2 clarifying questions to understand their situation and what they want to achieve.
Be direct and specific. Ask about current state, target outcome, constraints.
Keep it to 2-3 sentences. Don't ask for information you already have.
Do NOT use markdown formatting."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        return self._clean_markdown(message.content[0].text)

    def break_down_goal(self, goal_name: str, goal_description: str,
                        deadline: str = None) -> str:
        """Break down a goal into actionable tasks (legacy one-shot method)."""

        prompt = f"""Break down this goal into specific, actionable tasks.
Today's date is {self._today()}.

Goal: {goal_name}
Description: {goal_description}
Deadline: {deadline or 'Not specified'}

For each task: description, estimated hours, suggested due date.
Return as a simple numbered list. 5-10 tasks max. Be practical."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        return self._clean_markdown(message.content[0].text)

    def generate_tasks_from_context(self, goal_name: str, goal_description: str,
                                     goal_context: str, user_profile: dict,
                                     deadline: str = None) -> list:
        """Generate personalized tasks based on goal context and user profile.

        Returns list of task dicts with description, estimated_hours, due_date.
        """

        prompt = f"""Generate specific, actionable tasks for this goal.

IMPORTANT: Today's date is {self._today()}. All due dates must be today or later.

Goal: {goal_name}
Description: {goal_description}
Deadline: {deadline or 'Not specified'}

User Profile:
{json.dumps(user_profile, indent=2) if user_profile else 'None'}

Goal-Specific Context (from conversation):
{goal_context}

Return ONLY a JSON array. Each task:
- "description": specific action
- "estimated_hours": realistic estimate
- "due_date": YYYY-MM-DD or null

Example:
[
  {{"description": "Task 1", "estimated_hours": 2.5, "due_date": "2026-02-15"}},
  {{"description": "Task 2", "estimated_hours": 3, "due_date": null}}
]

5-10 tasks. Realistic and specific to their situation."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        response = message.content[0].text

        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                return []
        return []

    # ------------------------------------------------------------------
    # Profile learning
    # ------------------------------------------------------------------

    def extract_profile_updates(self, conversation_history: list, category: str) -> dict:
        """Analyze conversation and extract facts to update user profile."""

        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in conversation_history
        ])

        prompt = f"""Analyze this conversation and extract user facts for their profile.

Category: {category}

Conversation:
{conversation_text}

Extract generally-true facts (not goal-specific):
- Current role, experience level, company
- Skills, strengths, weaknesses
- Time availability, constraints

Return ONLY a JSON object. Field names:
- current_role, experience_years (number), current_company
- strengths (array), weaknesses (array)
- target_companies (array), target_roles (array)
- availability_hours_per_day (number)

Only include fields explicitly mentioned. Empty object if nothing to extract.
"""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        json_match = re.search(r'\{.*\}', message.content[0].text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                return {}
        return {}
