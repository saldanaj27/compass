import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path="agent.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
    
    def create_tables(self):
        # Goals table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                deadline DATE,
                status TEXT DEFAULT 'active',
                category TEXT DEFAULT 'general',
                context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Add columns to existing tables if they don't exist (migration)
        try:
            self.conn.execute("ALTER TABLE goals ADD COLUMN category TEXT DEFAULT 'general'")
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            self.conn.execute("ALTER TABLE goals ADD COLUMN context TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Tasks table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER,
                description TEXT NOT NULL,
                status TEXT DEFAULT 'todo',
                estimated_hours REAL,
                due_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (goal_id) REFERENCES goals (id)
            )
        """)
        
        # Daily logs table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                task_id INTEGER,
                hours_spent REAL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        """)
        
        self.conn.commit()
    
    def add_goal(self, name: str, description: str = "", deadline: str = None, category: str = "general", context: str = None) -> int:
        cursor = self.conn.execute(
            "INSERT INTO goals (name, description, deadline, category, context) VALUES (?, ?, ?, ?, ?)",
            (name, description, deadline, category, context)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def get_all_goals(self, status: str = "active") -> List[Dict]:
        cursor = self.conn.execute(
            "SELECT * FROM goals WHERE status = ? ORDER BY created_at DESC",
            (status,)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def add_task(self, goal_id: int, description: str, estimated_hours: float = None, due_date: str = None) -> int:
        cursor = self.conn.execute(
            "INSERT INTO tasks (goal_id, description, estimated_hours, due_date) VALUES (?, ?, ?, ?)",
            (goal_id, description, estimated_hours, due_date)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def get_tasks_for_goal(self, goal_id: int, status: str = None) -> List[Dict]:
        if status:
            cursor = self.conn.execute(
                "SELECT * FROM tasks WHERE goal_id = ? AND status = ? ORDER BY created_at",
                (goal_id, status)
            )
        else:
            cursor = self.conn.execute(
                "SELECT * FROM tasks WHERE goal_id = ? ORDER BY created_at",
                (goal_id,)
            )
        return [dict(row) for row in cursor.fetchall()]
    
    def log_progress(self, task_id: int, hours_spent: float, notes: str = "", date: str = None):
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        self.conn.execute(
            "INSERT INTO daily_logs (date, task_id, hours_spent, notes) VALUES (?, ?, ?, ?)",
            (date, task_id, hours_spent, notes)
        )
        self.conn.commit()

    def delete_task(self, task_id: int):
      self.conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
      self.conn.commit()

    def delete_goal(self, goal_id: int):
      # Delete all tasks for this goal first
      self.conn.execute("DELETE FROM tasks WHERE goal_id = ?", (goal_id,))
      self.conn.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
      self.conn.commit()


    def complete_task(self, task_id: int):
      self.conn.execute(
          "UPDATE tasks SET status = 'done', completed_at = ? WHERE id = ?",
          (datetime.now(), task_id)
      )
      self.conn.commit()

    def uncomplete_task(self, task_id: int):
      self.conn.execute(
          "UPDATE tasks SET status = 'todo', completed_at = NULL WHERE id = ?",
          (task_id,)
      )
      self.conn.commit()

    def get_todays_tasks(self) -> List[Dict]:
        """Get all tasks due today"""
        today = datetime.now().strftime("%Y-%m-%d")
        cursor = self.conn.execute(
            "SELECT * FROM tasks WHERE due_date = ? ORDER BY created_at",
            (today,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_yesterdays_completed_tasks(self) -> List[Dict]:
        """Get tasks completed yesterday"""
        from datetime import timedelta
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        cursor = self.conn.execute(
            """SELECT t.* FROM tasks t
               WHERE DATE(t.completed_at) = ?
               ORDER BY t.completed_at""",
            (yesterday,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_overdue_tasks(self) -> List[Dict]:
        """Get all tasks that are past due date and not completed"""
        today = datetime.now().strftime("%Y-%m-%d")
        cursor = self.conn.execute(
            """SELECT * FROM tasks
               WHERE due_date < ? AND status != 'done'
               ORDER BY due_date""",
            (today,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_all_active_tasks(self) -> List[Dict]:
        """Get all tasks that are not completed"""
        cursor = self.conn.execute(
            "SELECT * FROM tasks WHERE status != 'done' ORDER BY created_at"
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_goal(self, goal_id: int) -> Optional[Dict]:
        """Get a specific goal by ID"""
        cursor = self.conn.execute(
            "SELECT * FROM goals WHERE id = ?",
            (goal_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_goal_context(self, goal_id: int, context: str):
        """Update the context for a specific goal"""
        self.conn.execute(
            "UPDATE goals SET context = ? WHERE id = ?",
            (context, goal_id)
        )
        self.conn.commit()