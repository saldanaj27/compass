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
    
    def daily_checkin(self, context: dict) -> str:
        """Conduct daily check-in conversation"""
        
        prompt = f"""You are a personal productivity agent conducting a daily check-in.

        Context:
        - Active goals: {context.get('goals', [])}
        - Yesterday's tasks: {context.get('yesterday_tasks', [])}
        - Today's planned tasks: {context.get('today_tasks', [])}

        Have a brief, friendly check-in conversation. Ask:
        1. What they accomplished yesterday
        2. Any blockers or challenges
        3. Confirm today's plan

        Keep it conversational and encouraging. Be brief (3-4 sentences max)."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response = message.content[0].text
        return self._clean_markdown(response)