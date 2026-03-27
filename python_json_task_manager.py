"""Simple CLI To-Do List Manager using a JSON file for storage."""
"""Author: Thomas Bagnardi"""
"""Date: 01-24-2026"""

import argparse
import os
import json
import configparser
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
from rich.console import Console
from rich.table import Table
from rich.style import Style

console = Console()

# Configure logging
log_file = Path.home() / ".task_manager.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(str(log_file)),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Task:
    """Represents a single task with metadata and optional subtasks."""
    
    def __init__(self, title: str, date: Optional[str] = None, time: Optional[str] = None, priority: Optional[str] = None, category: Optional[str] = None, done: bool = False, subtasks: Optional[List["Task"]] = None, category_emojis: Optional[Dict[str, str]] = None, priority_emojis: Optional[Dict[str, str]] = None) -> None:
        """Initialize a task with the given properties."""
        self.title = title
        self.date = date
        self.time = time
        self.priority = priority
        self.category = category
        self.done = done
        self.subtasks = subtasks or []
        self.category_emojis = category_emojis or {}
        self.priority_emojis = priority_emojis or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for JSON serialization, including nested subtasks."""
        return {
            "done": self.done,
            "title": self.title,
            "date": self.date if self.date else None,
            "time": self.time if self.time else None,
            "priority": self.priority if self.priority else None,
            "category": self.category if self.category else None,
            "subtasks": [subtask.to_dict() for subtask in self.subtasks]
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any], category_emojis: Optional[Dict[str, str]] = None, priority_emojis: Optional[Dict[str, str]] = None) -> "Task":
        """Create a Task instance from a dictionary, recursively handling nested subtasks."""
        subtasks_data = data.get("subtasks", [])
        subtasks = [Task.from_dict(subtask_data, category_emojis, priority_emojis) for subtask_data in subtasks_data]
        
        return Task(
            title=data.get("title"),
            date=data.get("date"),
            time=data.get("time"),
            priority=data.get("priority"),
            category=data.get("category"),
            done=data.get("done", False),
            subtasks=subtasks,
            category_emojis=category_emojis,
            priority_emojis=priority_emojis
        )
    
    def format_display(self, task_number: int) -> str:
        """Format task for display in the list."""
        mark = "[x]" if self.done else "[ ]"
        display = f"{task_number}. {mark} {self.title}"
        
        if self.category:
            category_emoji = {"work": "💼", "personal": "🏠"}.get(self.category, "")
            display += f" {category_emoji}"
        
        if self.priority:
            priority_emoji = {"low": "🔵", "medium": "🟡", "high": "🔴"}.get(self.priority, "")
            display += f" {priority_emoji}"
        
        if self.date:
            display += f" (📅 {self.date}"
            if self.time:
                display += f" {self.time}"
            display += ")"
        
        return display
    
    def mark_done(self) -> None:
        """Mark this task as done."""
        self.done = True


class TaskManager:
    """Manages all task operations including loading, saving, and displaying."""
    
    def __init__(self, db_file: Optional[str] = None, config_file: str = "config.ini") -> None:
        """Initialize the task manager with the given database file."""
        if db_file is None:
            db_file = Path.home() / ".tasks.json"
        else:
            db_file = Path(db_file)
        self.db_file = db_file
        self.config_file = config_file
        self.category_emojis, self.priority_emojis = self.load_config()
        self.tasks = self.load()
    
    def load_config(self) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Load emoji configuration from the config file."""
        config = configparser.ConfigParser()
        config_path = Path(__file__).parent / self.config_file
        
        category_emojis = {}
        priority_emojis = {}
        
        try:
            if config_path.exists():
                config.read(config_path)
                
                if "categories" in config:
                    category_emojis = dict(config["categories"])
                
                if "priorities" in config:
                    priority_emojis = dict(config["priorities"])
            else:
                console.print(f"[yellow]Warning: Config file not found at {config_path}. Using default emojis.[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Warning: Error loading config file: {e}. Using default emojis.[/yellow]")
        
        return category_emojis, priority_emojis
    
    def load(self) -> List[Task]:
        """Load tasks from the JSON file."""
        if not self.db_file.exists():
            return []
        
        try:
            with open(self.db_file, "r") as f:
                tasks_data = json.load(f)
            return [Task.from_dict(task_data, self.category_emojis, self.priority_emojis) for task_data in tasks_data]
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {self.db_file}: {e}")
            return []
        except IOError as e:
            logger.error(f"Error reading {self.db_file}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error loading tasks: {e}")
            return []
    
    def save(self) -> None:
        """Save all tasks to the JSON file and create a timestamped backup."""
        # Save main tasks file
        with open(self.db_file, "w") as f:
            tasks_data = [task.to_dict() for task in self.tasks]
            json.dump(tasks_data, f, indent=2)
        
        # Create timestamped backup in hidden backup folder
        self._create_backup()
    
    def _create_backup(self) -> None:
        """Create a timestamped backup of the tasks file."""
        try:
            # Create backup directory if it doesn't exist
            backup_dir = Path.home() / ".task_manager" / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate timestamped backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f".tasks.json.backup_{timestamp}"
            
            # Copy current tasks file to backup
            if self.db_file.exists():
                with open(self.db_file, "r") as source:
                    with open(backup_file, "w") as destination:
                        destination.write(source.read())
                logger.info(f"Backup created: {backup_file}")
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
    
    def add_task(self, title: str, date: Optional[str] = None, time: Optional[str] = None, priority: Optional[str] = None, category: Optional[str] = None) -> None:
        """Add a new task and display confirmation."""
        # Parse and validate date if provided
        if date:
            try:
                # Try to parse natural language dates
                parsed_date = date_parser.parse(date, fuzzy=False)
                date = parsed_date.strftime("%Y-%m-%d")
            except (ValueError, date_parser.ParserError):
                # Check if it's a special keyword
                date_lower = date.lower()
                today = datetime.now().date()
                
                if date_lower == "today":
                    date = today.strftime("%Y-%m-%d")
                elif date_lower == "tomorrow":
                    tomorrow = today + relativedelta(days=1)
                    date = tomorrow.strftime("%Y-%m-%d")
                else:
                    console.print(f"[red]Error: Could not parse date '{date}'. Try 'today', 'tomorrow', or YYYY-MM-DD format.[/red]")
                    return
        
        # Validate time format if provided
        if time:
            try:
                datetime.strptime(time, "%H:%M")
            except ValueError:
                console.print(f"[red]Error: Invalid time format '{time}'. Please use HH:MM format.[/red]")
                return
        
        task = Task(title, date, time, priority, category, category_emojis=self.category_emojis, priority_emojis=self.priority_emojis)
        self.tasks.append(task)
        self.save()
        
        console.print(f"[green]✓ Added task: {title}[/green]")
        if category:
            console.print(f"  [cyan]Category:[/cyan] {category}")
        if priority:
            console.print(f"  [cyan]Priority:[/cyan] {priority}")
        if date:
            output = f"  [cyan]Due:[/cyan] {date}"
            if time:
                output += f" at {time}"
            console.print(output)
    
    def list_tasks(self, only_work: bool = False, only_personal: bool = False, pending: bool = False) -> None:
        """Display all tasks sorted by priority and date with optional filters."""
        # Apply filters
        filtered_tasks = self.tasks
        
        if only_work:
            filtered_tasks = [task for task in filtered_tasks if task.category == "work"]
        
        if only_personal:
            filtered_tasks = [task for task in filtered_tasks if task.category == "personal"]
        
        if pending:
            filtered_tasks = [task for task in filtered_tasks if not task.done]
        
        if not filtered_tasks:
            console.print("[yellow]List is empty.[/yellow]")
        else:
            # Define priority order for sorting (high > medium > low)
            priority_order = {"high": 0, "medium": 1, "low": 2, None: 3}
            
            # Sort tasks by priority first, then by date
            sorted_tasks = sorted(
                filtered_tasks,
                key=lambda task: (
                    priority_order.get(task.priority, 3),
                    task.date if task.date else "9999-12-31"
                )
            )
            
            # Create rich table
            table = Table(title="Tasks", show_header=True, header_style="bold magenta")
            table.add_column("ID", style="cyan", width=5)
            table.add_column("Done", style="green", width=6)
            table.add_column("Task", style="white")
            table.add_column("Category", width=12)
            table.add_column("Priority", width=10)
            table.add_column("Due Date", width=12)
            table.add_column("Time", width=8)
            
            for i, task in enumerate(sorted_tasks, 1):
                # Determine priority color
                priority_color = {
                    "high": "red",
                    "medium": "yellow",
                    "low": "green",
                    None: "white"
                }.get(task.priority, "white")
                
                priority_text = f"[{priority_color}]{task.priority if task.priority else '-'}[/{priority_color}]"
                
                # Category emoji from config
                category_emoji = self.category_emojis.get(task.category, "-") if task.category else "-"
                
                # Done status
                done_text = "[green]✓[/green]" if task.done else "[ ]"
                
                table.add_row(
                    str(i),
                    done_text,
                    task.title,
                    category_emoji,
                    priority_text,
                    task.date if task.date else "-",
                    task.time if task.time else "-"
                )
            
            console.print(table)
    
    def mark_done(self, task_id: int) -> None:
        """Mark a task as done by its ID."""
        if 0 < task_id <= len(self.tasks):
            self.tasks[task_id - 1].mark_done()
            self.save()
            console.print(f"[green]✓ Marked task {task_id} as done.[/green]")
        else:
            console.print("[red]Invalid task ID.[/red]")
    
    def delete_task(self, task_id: int) -> None:
        """Delete a task by its ID."""
        if 0 < task_id <= len(self.tasks):
            deleted_task = self.tasks.pop(task_id - 1)
            self.save()
            console.print(f"[yellow]✓ Deleted task: {deleted_task.title}[/yellow]")
        else:
            console.print("[red]Invalid task ID.[/red]")
    
    def search_tasks(self, query: str, use_regex: bool = False) -> None:
        """Search for tasks by title using string matching or regex."""
        results = []
        
        try:
            if use_regex:
                pattern = re.compile(query, re.IGNORECASE)
                results = [task for task in self.tasks if pattern.search(task.title)]
            else:
                # Case-insensitive string matching
                query_lower = query.lower()
                results = [task for task in self.tasks if query_lower in task.title.lower()]
        except re.error as e:
            console.print(f"[red]Invalid regex pattern: {e}[/red]")
            return
        
        if not results:
            console.print(f"[yellow]No tasks found matching '{query}'[/yellow]")
        else:
            # Display results in a table
            table = Table(title=f"Search Results ({len(results)} found)", show_header=True, header_style="bold magenta")
            table.add_column("ID", style="cyan", width=5)
            table.add_column("Done", style="green", width=6)
            table.add_column("Task", style="white")
            table.add_column("Category", width=12)
            table.add_column("Priority", width=10)
            table.add_column("Due Date", width=12)
            table.add_column("Time", width=8)
            
            for i, task in enumerate(results, 1):
                # Determine priority color
                priority_color = {
                    "high": "red",
                    "medium": "yellow",
                    "low": "green",
                    None: "white"
                }.get(task.priority, "white")
                
                priority_text = f"[{priority_color}]{task.priority if task.priority else '-'}[/{priority_color}]"
                
                # Category emoji from config
                category_emoji = self.category_emojis.get(task.category, "-") if task.category else "-"
                
                # Done status
                done_text = "[green]✓[/green]" if task.done else "[ ]"
                
                table.add_row(
                    str(i),
                    done_text,
                    task.title,
                    category_emoji,
                    priority_text,
                    task.date if task.date else "-",
                    task.time if task.time else "-"
                )
            
            console.print(table)

def main():
    parser = argparse.ArgumentParser(description="Simple Python CLI To-Do List (JSON version)")
    subparsers = parser.add_subparsers(dest="command")
    
    # Add command
    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("title", type=str)
    add_parser.add_argument("--date", type=str, help="Due date (YYYY-MM-DD)")
    add_parser.add_argument("--time", type=str, help="Due time (HH:MM)")
    add_parser.add_argument("--priority", type=str, choices=["low", "medium", "high"], help="Task priority")
    add_parser.add_argument("--category", type=str, choices=["work", "personal"], help="Task category")
    
    # List command
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--only-work", action="store_true", help="Show only work tasks")
    list_parser.add_argument("--only-personal", action="store_true", help="Show only personal tasks")
    list_parser.add_argument("--pending", action="store_true", help="Show only incomplete tasks")
    
    # Done command
    done_parser = subparsers.add_parser("done")
    done_parser.add_argument("id", type=int, help="Task number to mark as done")
    
    # Delete command
    del_parser = subparsers.add_parser("delete")
    del_parser.add_argument("id", type=int, help="Task number to delete")
    
    # Search command
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("query", type=str, help="Search query for task title")
    search_parser.add_argument("--regex", action="store_true", help="Use regex pattern matching instead of simple string matching")
    
    args = parser.parse_args()
    manager = TaskManager()
    
    if args.command == "add":
        manager.add_task(
            title=args.title,
            date=args.date,
            time=args.time,
            priority=args.priority,
            category=args.category
        )
    elif args.command == "list":
        manager.list_tasks(
            only_work=args.only_work,
            only_personal=args.only_personal,
            pending=args.pending
        )
    elif args.command == "done":
        manager.mark_done(args.id)
    elif args.command == "delete":
        manager.delete_task(args.id)
    elif args.command == "search":
        manager.search_tasks(args.query, use_regex=args.regex)
            
if __name__ == "__main__":
    main()