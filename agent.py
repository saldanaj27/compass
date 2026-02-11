import os, re
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

class Agent:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-sonnet-4-20250514"
    
    def _clean_markdown(self, text: str) -> str:
        """Remove markdown formatting for CLI display"""
        # Remove bold/italic
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # **bold**
        text = re.sub(r'\*(.+?)\*', r'\1', text)      # *italic*
        text = re.sub(r'__(.+?)__', r'\1', text)      # __bold__
        text = re.sub(r'_(.+?)_', r'\1', text)        # _italic_
        return text

    def break_down_goal(self, goal_name: str, goal_description: str, deadline: str = None) -> list:
        """Break down a goal into actionable tasks"""
        
        prompt = f"""You are a personal productivity agent. Break down this goal into specific, actionable tasks.

        Goal: {goal_name}
        Description: {goal_description}
        Deadline: {deadline or 'Not specified'}

        For each task, provide:
        1. Task description (specific and actionable)
        2. Estimated hours needed
        3. Suggested due date (if deadline provided)

        Return as a simple numbered list, format:
        1. [Task description] - [X hours] - [Due date if applicable]

        Be practical and realistic. Be cognizant of the current date (if deadline provided). Break it into 5-10 tasks max."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response = message.content[0].text
        return self._clean_markdown(response)
    
    def daily_checkin_greeting(self, context: dict) -> str:
        """Generate opening greeting for daily check-in

        This is just the first message. Use conversation_turn() for follow-ups.
        """

        prompt = f"""You are starting a daily check-in conversation. Be direct and firm.

Context:
- Active goals: {[g['name'] for g in context.get('goals', [])]}
- Yesterday's completed tasks: {len(context.get('yesterday_tasks', []))} tasks
- Today's planned tasks: {len(context.get('today_tasks', []))} tasks
- Overdue tasks: {len(context.get('overdue_tasks', []))} tasks

Start the conversation with a brief, direct greeting (2-3 sentences).
Reference specific context (overdue tasks, yesterday's work, etc.).
Ask what they're working on today."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        response = message.content[0].text
        return self._clean_markdown(response)

    def conversation_turn(self, message_history: list, user_message: str, context: dict = None) -> str:
        """Handle one turn of a multi-turn conversation

        Args:
            message_history: List of {"role": "user"|"assistant", "content": "..."}
            user_message: Latest message from user
            context: Optional context dict with goals, tasks, etc.

        Returns:
            Agent's response to this turn
        """

        # Build system prompt with context if provided
        system_prompt = """You are a direct, firm accountability agent. Your job is to keep the user on track with their goals.

Be conversational but don't waste words. Ask pointed questions about progress and blockers.
If user committed to something, hold them to it (respectfully but firmly).
If user is avoiding work, ask what's really getting in the way.

Keep responses to 2-3 sentences. Be helpful but direct."""

        if context:
            system_prompt += f"\n\nCurrent context:\n"
            if context.get('goals'):
                system_prompt += f"- Active goals: {', '.join([g['name'] for g in context['goals']])}\n"
            if context.get('overdue_tasks'):
                system_prompt += f"- Overdue tasks: {len(context['overdue_tasks'])} tasks are past due\n"
            if context.get('today_tasks'):
                system_prompt += f"- Today's tasks: {len(context['today_tasks'])} tasks due today\n"

        # Add user's latest message to history
        message_history.append({"role": "user", "content": user_message})

        # Call Claude with full conversation history
        message = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            system=system_prompt,
            messages=message_history
        )

        response = message.content[0].text
        return self._clean_markdown(response)

    def goal_discovery_greeting(self, goal_name: str, user_profile: dict, category: str = "general") -> str:
        """Start discovery conversation for a new goal

        Args:
            goal_name: The goal the user wants to achieve
            user_profile: User's global profile data
            category: Goal category (career, health, finance, etc.)

        Returns:
            Opening question to start discovery conversation
        """

        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")

        profile_context = ""
        if user_profile and category in user_profile:
            profile_context = f"\n\nI know from your profile:\n"
            for key, value in user_profile[category].items():
                if value:  # Only include non-empty values
                    profile_context += f"- {key}: {value}\n"

        prompt = f"""You are helping a user set up a new goal: "{goal_name}"
Today's date: {today}
Category: {category}
{profile_context}

Your job is to ask 1-2 clarifying questions to understand their current situation and what they want to achieve.

Be direct and specific. Ask about:
- Current state (where are they now?)
- Target outcome (where do they want to be?)
- Constraints (time, resources, blockers?)

Keep it to 2-3 sentences. Don't ask for information you already have from the profile."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        response = message.content[0].text
        return self._clean_markdown(response)

    def generate_tasks_from_context(self, goal_name: str, goal_description: str, goal_context: str, user_profile: dict, deadline: str = None) -> list:
        """Generate personalized tasks based on goal context and user profile

        Args:
            goal_name: Name of the goal
            goal_description: Description of the goal
            goal_context: Context gathered from discovery conversation (JSON string)
            user_profile: User's global profile
            deadline: Optional deadline

        Returns:
            List of task dictionaries with description, estimated_hours, due_date
        """

        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")

        prompt = f"""You are a personal productivity agent. Generate specific, actionable tasks for this goal.

IMPORTANT: Today's date is {today}. Use this when setting due dates.

Goal: {goal_name}
Description: {goal_description}
Deadline: {deadline or 'Not specified'}

User Profile:
{user_profile}

Goal-Specific Context (from conversation):
{goal_context}

Based on the user's specific situation and context, create personalized tasks.

IMPORTANT: Return ONLY a JSON array of tasks. Each task should have:
- "description": specific action to take
- "estimated_hours": realistic estimate
- "due_date": suggested date (YYYY-MM-DD format, or null if no deadline)

Format:
[
  {{"description": "Task 1", "estimated_hours": 2.5, "due_date": "2026-02-15"}},
  {{"description": "Task 2", "estimated_hours": 3, "due_date": null}}
]

Create 5-10 tasks. Be realistic and specific to their situation."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        response = message.content[0].text

        # Extract JSON from response (in case there's extra text)
        import json
        import re

        # Try to find JSON array in response
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            try:
                tasks = json.loads(json_match.group())
                return tasks
            except json.JSONDecodeError:
                # Fallback to old format if JSON parsing fails
                return []

        return []

    def extract_profile_updates(self, conversation_history: list, category: str) -> dict:
        """Analyze conversation and extract facts that should update user profile

        Args:
            conversation_history: Full conversation between user and agent
            category: Goal category (career, health, etc.)

        Returns:
            Dictionary of profile updates for the category
        """

        # Build conversation summary
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in conversation_history
        ])

        prompt = f"""Analyze this conversation and extract user facts that should be saved to their profile.

Category: {category}

Conversation:
{conversation_text}

Extract any facts the user mentioned about themselves that are generally true (not goal-specific):
- Current role, experience level, company
- Skills, strengths, weaknesses
- Time availability, constraints
- Preferences, learning style
- Long-term goals or aspirations

Return ONLY a JSON object with extracted facts. Use these field names:
- current_role
- experience_years (number)
- current_company
- strengths (array)
- weaknesses (array)
- target_companies (array)
- target_roles (array)
- availability_hours_per_day (number)

Only include fields where the user explicitly mentioned information. Return empty object if nothing to extract.

Example:
{{"current_role": "Software Engineer", "experience_years": 3, "strengths": ["backend", "APIs"], "weaknesses": ["system design"]}}
"""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        response = message.content[0].text

        # Extract JSON
        import json
        import re

        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                updates = json.loads(json_match.group())
                return updates
            except json.JSONDecodeError:
                return {}

        return {}