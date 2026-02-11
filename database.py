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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tasks table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER,
                description TEXT NOT NULL,
                status TEXT DEFAULT 'todo',
                priority TEXT DEFAULT 'medium',
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
    
    def add_goal(self, name: str, description: str = "", deadline: str = None) -> int:
        cursor = self.conn.execute(
            "INSERT INTO goals (name, description, deadline) VALUES (?, ?, ?)",
            (name, description, deadline)
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