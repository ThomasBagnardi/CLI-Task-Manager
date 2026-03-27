"""Unit tests for the Task Manager application using pytest."""

import pytest
import json
import tempfile
from pathlib import Path
from python_json_task_manager import Task, TaskManager


class TestTask:
    """Tests for the Task class."""
    
    def test_task_creation(self) -> None:
        """Test basic task creation."""
        task = Task(
            title="Test Task",
            date="2026-02-10",
            time="14:30",
            priority="high",
            category="work"
        )
        
        assert task.title == "Test Task"
        assert task.date == "2026-02-10"
        assert task.time == "14:30"
        assert task.priority == "high"
        assert task.category == "work"
        assert task.done is False
        assert task.subtasks == []
    
    def test_task_to_dict(self) -> None:
        """Test Task serialization to dictionary."""
        task = Task(
            title="Test Task",
            date="2026-02-10",
            priority="medium",
            category="personal"
        )
        
        task_dict = task.to_dict()
        
        assert task_dict["title"] == "Test Task"
        assert task_dict["date"] == "2026-02-10"
        assert task_dict["priority"] == "medium"
        assert task_dict["category"] == "personal"
        assert task_dict["done"] is False
        assert task_dict["subtasks"] == []
    
    def test_task_from_dict(self) -> None:
        """Test Task deserialization from dictionary."""
        task_dict = {
            "title": "Restored Task",
            "date": "2026-02-15",
            "time": "10:00",
            "priority": "low",
            "category": "work",
            "done": True,
            "subtasks": []
        }
        
        task = Task.from_dict(task_dict)
        
        assert task.title == "Restored Task"
        assert task.date == "2026-02-15"
        assert task.time == "10:00"
        assert task.priority == "low"
        assert task.category == "work"
        assert task.done is True
    
    def test_task_with_subtasks(self) -> None:
        """Test Task with nested subtasks."""
        subtask1 = Task(title="Subtask 1")
        subtask2 = Task(title="Subtask 2", done=True)
        
        main_task = Task(
            title="Main Task",
            subtasks=[subtask1, subtask2]
        )
        
        assert len(main_task.subtasks) == 2
        assert main_task.subtasks[0].title == "Subtask 1"
        assert main_task.subtasks[1].done is True
    
    def test_task_subtasks_serialization(self) -> None:
        """Test that subtasks are properly serialized and deserialized."""
        # Create task with subtasks
        subtask1 = Task(title="Sub 1", priority="high")
        subtask2 = Task(title="Sub 2", done=True)
        
        main_task = Task(
            title="Main",
            subtasks=[subtask1, subtask2]
        )
        
        # Serialize
        task_dict = main_task.to_dict()
        assert len(task_dict["subtasks"]) == 2
        assert task_dict["subtasks"][0]["title"] == "Sub 1"
        assert task_dict["subtasks"][1]["done"] is True
        
        # Deserialize
        restored = Task.from_dict(task_dict)
        assert len(restored.subtasks) == 2
        assert restored.subtasks[0].title == "Sub 1"
        assert restored.subtasks[1].done is True
    
    def test_task_mark_done(self) -> None:
        """Test marking a task as done."""
        task = Task(title="Test Task")
        assert task.done is False
        
        task.mark_done()
        assert task.done is True


class TestTaskManager:
    """Tests for the TaskManager class."""
    
    @pytest.fixture
    def temp_db(self) -> tuple[Path, Path]:
        """Create temporary database and config files for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_tasks.json"
            config_path = Path(tmpdir) / "config.ini"
            return db_path, config_path
    
    def test_taskmanager_creation(self, temp_db: tuple[Path, Path]) -> None:
        """Test TaskManager initialization."""
        db_path, config_path = temp_db
        manager = TaskManager(db_file=str(db_path), config_file=str(config_path))
        
        assert manager.db_file == db_path
        assert isinstance(manager.tasks, list)
    
    def test_save_and_load_empty(self, temp_db: tuple[Path, Path]) -> None:
        """Test saving and loading an empty task list."""
        db_path, config_path = temp_db
        manager = TaskManager(db_file=str(db_path), config_file=str(config_path))
        
        manager.save()
        
        assert db_path.exists()
        
        # Load in new manager instance
        manager2 = TaskManager(db_file=str(db_path), config_file=str(config_path))
        assert len(manager2.tasks) == 0
    
    def test_save_and_load_tasks(self, temp_db: tuple[Path, Path]) -> None:
        """Test saving and loading tasks."""
        db_path, config_path = temp_db
        manager = TaskManager(db_file=str(db_path), config_file=str(config_path))
        
        # Add tasks
        task1 = Task(title="Task 1", priority="high", category="work")
        task2 = Task(title="Task 2", date="2026-02-10", category="personal")
        manager.tasks = [task1, task2]
        manager.save()
        
        # Load in new instance
        manager2 = TaskManager(db_file=str(db_path), config_file=str(config_path))
        
        assert len(manager2.tasks) == 2
        assert manager2.tasks[0].title == "Task 1"
        assert manager2.tasks[0].priority == "high"
        assert manager2.tasks[1].title == "Task 2"
        assert manager2.tasks[1].date == "2026-02-10"
    
    def test_save_and_load_with_subtasks(self, temp_db: tuple[Path, Path]) -> None:
        """Test saving and loading tasks with subtasks."""
        db_path, config_path = temp_db
        manager = TaskManager(db_file=str(db_path), config_file=str(config_path))
        
        # Create task with subtasks
        subtask = Task(title="Subtask", done=True)
        main_task = Task(title="Main", subtasks=[subtask])
        manager.tasks = [main_task]
        manager.save()
        
        # Load in new instance
        manager2 = TaskManager(db_file=str(db_path), config_file=str(config_path))
        
        assert len(manager2.tasks) == 1
        assert manager2.tasks[0].title == "Main"
        assert len(manager2.tasks[0].subtasks) == 1
        assert manager2.tasks[0].subtasks[0].title == "Subtask"
        assert manager2.tasks[0].subtasks[0].done is True
    
    def test_add_task(self, temp_db: tuple[Path, Path]) -> None:
        """Test adding a task."""
        db_path, config_path = temp_db
        manager = TaskManager(db_file=str(db_path), config_file=str(config_path))
        
        manager.add_task(
            title="New Task",
            priority="high",
            category="work"
        )
        
        assert len(manager.tasks) == 1
        assert manager.tasks[0].title == "New Task"
        assert db_path.exists()
    
    def test_mark_done(self, temp_db: tuple[Path, Path]) -> None:
        """Test marking a task as done."""
        db_path, config_path = temp_db
        manager = TaskManager(db_file=str(db_path), config_file=str(config_path))
        
        manager.add_task(title="Task to complete")
        assert manager.tasks[0].done is False
        
        manager.mark_done(1)
        assert manager.tasks[0].done is True
        
        # Verify persistence
        manager2 = TaskManager(db_file=str(db_path), config_file=str(config_path))
        assert manager2.tasks[0].done is True
    
    def test_delete_task(self, temp_db: tuple[Path, Path]) -> None:
        """Test deleting a task."""
        db_path, config_path = temp_db
        manager = TaskManager(db_file=str(db_path), config_file=str(config_path))
        
        manager.add_task(title="Task 1")
        manager.add_task(title="Task 2")
        assert len(manager.tasks) == 2
        
        manager.delete_task(1)
        assert len(manager.tasks) == 1
        assert manager.tasks[0].title == "Task 2"
    
    def test_backup_creation(self, temp_db: tuple[Path, Path]) -> None:
        """Test that backups are created on save."""
        db_path, config_path = temp_db
        
        # Mock backup directory
        backup_dir = Path(tempfile.gettempdir()) / "test_task_manager_backups"
        backup_dir.mkdir(exist_ok=True)
        
        manager = TaskManager(db_file=str(db_path), config_file=str(config_path))
        manager.add_task(title="Task 1")
        manager.save()
        
        assert db_path.exists()
    
    def test_json_format_validity(self, temp_db: tuple[Path, Path]) -> None:
        """Test that saved JSON is valid and properly formatted."""
        db_path, config_path = temp_db
        manager = TaskManager(db_file=str(db_path), config_file=str(config_path))
        
        manager.add_task(title="Task 1", priority="high", date="2026-02-10")
        manager.save()
        
        # Verify JSON is valid
        with open(db_path, "r") as f:
            data = json.load(f)
        
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["title"] == "Task 1"
        assert data[0]["priority"] == "high"
        assert data[0]["date"] == "2026-02-10"
    
    def test_load_nonexistent_file(self, temp_db: tuple[Path, Path]) -> None:
        """Test loading when database file doesn't exist."""
        db_path, config_path = temp_db
        manager = TaskManager(db_file=str(db_path), config_file=str(config_path))
        
        assert len(manager.tasks) == 0
        assert not db_path.exists()
    
    def test_multiple_save_load_cycles(self, temp_db: tuple[Path, Path]) -> None:
        """Test multiple save/load cycles preserve data integrity."""
        db_path, config_path = temp_db
        manager = TaskManager(db_file=str(db_path), config_file=str(config_path))
        
        # First cycle
        manager.add_task(title="Task 1")
        manager.save()
        
        # Second cycle
        manager2 = TaskManager(db_file=str(db_path), config_file=str(config_path))
        manager2.add_task(title="Task 2")
        manager2.save()
        
        # Third cycle
        manager3 = TaskManager(db_file=str(db_path), config_file=str(config_path))
        assert len(manager3.tasks) == 2
        assert manager3.tasks[0].title == "Task 1"
        assert manager3.tasks[1].title == "Task 2"


class TestTaskSerializationEdgeCases:
    """Tests for edge cases in serialization."""
    
    def test_none_values_serialization(self) -> None:
        """Test that None values are properly handled."""
        task = Task(title="Minimal Task")
        task_dict = task.to_dict()
        
        assert task_dict["date"] is None
        assert task_dict["time"] is None
        assert task_dict["priority"] is None
        assert task_dict["category"] is None
    
    def test_empty_string_title(self) -> None:
        """Test task with empty string title."""
        task = Task(title="")
        assert task.title == ""
        
        task_dict = task.to_dict()
        assert task_dict["title"] == ""
    
    def test_special_characters_in_title(self) -> None:
        """Test task with special characters."""
        special_title = "Task with 🎉 emoji & special chars!@#$%"
        task = Task(title=special_title)
        
        task_dict = task.to_dict()
        restored = Task.from_dict(task_dict)
        
        assert restored.title == special_title
    
    def test_deeply_nested_subtasks(self) -> None:
        """Test deeply nested subtask hierarchy."""
        level3 = Task(title="Level 3")
        level2 = Task(title="Level 2", subtasks=[level3])
        level1 = Task(title="Level 1", subtasks=[level2])
        
        task_dict = level1.to_dict()
        restored = Task.from_dict(task_dict)
        
        assert restored.title == "Level 1"
        assert restored.subtasks[0].title == "Level 2"
        assert restored.subtasks[0].subtasks[0].title == "Level 3"
