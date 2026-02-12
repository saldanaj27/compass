import os
import json
from pathlib import Path
from typing import Dict, Optional

class UserProfile:
    """Manages user-global context stored in ~/.compass/user_profile.json"""

    def __init__(self):
        self.compass_dir = Path.home() / ".compass"
        self.profile_path = self.compass_dir / "user_profile.json"
        self._ensure_directory()

    def _ensure_directory(self):
        """Create ~/.compass directory if it doesn't exist"""
        self.compass_dir.mkdir(exist_ok=True)

    def exists(self) -> bool:
        """Check if user profile exists"""
        return self.profile_path.exists()

    def load(self) -> Dict:
        """Load user profile, return empty dict if doesn't exist"""
        if not self.exists():
            return {}

        with open(self.profile_path, 'r') as f:
            return json.load(f)

    def save(self, profile_data: Dict):
        """Save user profile"""
        with open(self.profile_path, 'w') as f:
            json.dump(profile_data, f, indent=2)

    def update(self, updates: Dict):
        """Update specific fields in profile"""
        profile = self.load()
        profile.update(updates)
        self.save(profile)

    def get_category(self, category: str) -> Dict:
        """Get profile data for a specific category (career, health, etc.)"""
        profile = self.load()
        return profile.get(category, {})

    def update_category(self, category: str, data: Dict):
        """Update a specific category in the profile"""
        profile = self.load()
        if category not in profile:
            profile[category] = {}
        profile[category].update(data)
        self.save(profile)

    def get_summary(self) -> str:
        """Get a human-readable summary of the profile"""
        profile = self.load()

        if not profile:
            return "No user profile found."

        lines = []
        for category, data in profile.items():
            lines.append(f"\n{category.upper()}:")
            for key, value in data.items():
                lines.append(f"  - {key}: {value}")

        return "\n".join(lines)

    def initialize_default(self):
        """Create a default profile structure"""
        default_profile = {
            "general": {
                "name": "",
                "timezone": "",
                "availability_hours_per_day": 0,
                "availability_days_per_week": 0
            },
            "career": {
                "current_role": "",
                "experience_years": 0,
                "strengths": [],
                "weaknesses": [],
                "target_companies": [],
                "target_roles": []
            },
            "learning": {
                "learning_style": "",
                "preferred_resources": [],
                "current_focus": []
            },
            "health": {
                "fitness_level": "",
                "health_goals": []
            },
            "finance": {
                "financial_goals": [],
                "risk_tolerance": ""
            }
        }
        self.save(default_profile)
        return default_profile
