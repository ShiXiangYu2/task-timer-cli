"""Task Timer CLI - Track task execution time"""

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path


class TimerState(Enum):
    """Timer states"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"


@dataclass
class Record:
    """Time tracking record"""
    task: str
    start_time: datetime
    end_time: datetime | None = None
    issue_id: str | None = None
    paused_duration: timedelta = timedelta()

    @property
    def duration_seconds(self) -> int:
        """Calculate duration in seconds"""
        if self.end_time is None:
            return 0
        return int((self.end_time - self.start_time - self.paused_duration).total_seconds())

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "task": self.task,
            "issue_id": self.issue_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "paused_duration_seconds": int(self.paused_duration.total_seconds())
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Record":
        """Create from dictionary"""
        return cls(
            task=data["task"],
            issue_id=data.get("issue_id"),
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            paused_duration=timedelta(seconds=data.get("paused_duration_seconds", 0))
        )


class TaskTimer:
    """Task Timer main class"""

    def __init__(self, data_dir: str | None = None):
        """Initialize timer"""
        self.data_dir = Path(data_dir or os.path.expanduser("~/.task-timer"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.records_file = self.data_dir / "records.json"

        self.state = TimerState.IDLE
        self.current_task: str | None = None
        self.current_issue: str | None = None
        self.current_record: Record | None = None
        self.pause_time: datetime | None = None
        self.total_paused: timedelta = timedelta()

        self.records: list[Record] = self._load_records()

    def _load_records(self) -> list[Record]:
        """Load records from file"""
        if not self.records_file.exists():
            return []
        with open(self.records_file) as f:
            data = json.load(f)
            return [Record.from_dict(r) for r in data]

    def _save_records(self):
        """Save records to file"""
        with open(self.records_file, "w") as f:
            json.dump([r.to_dict() for r in self.records], f, indent=2)

    def start(self, task: str, issue_id: str | None = None):
        """Start a new timer - Issue #1"""
        # Stop any running timer first
        if self.state != TimerState.IDLE:
            self.stop()

        self.current_task = task
        self.current_issue = issue_id
        self.current_record = Record(
            task=task,
            issue_id=issue_id,
            start_time=datetime.now()
        )
        self.state = TimerState.RUNNING
        self.total_paused = timedelta()

    def pause(self):
        """Pause the current timer - Issue #2"""
        if self.state != TimerState.RUNNING:
            raise ValueError("No timer running")
        self.state = TimerState.PAUSED
        self.pause_time = datetime.now()

    def resume(self):
        """Resume a paused timer - Issue #2"""
        if self.state != TimerState.PAUSED:
            raise ValueError("Timer is not paused")
        if self.pause_time:
            self.total_paused += datetime.now() - self.pause_time
        self.state = TimerState.RUNNING
        self.pause_time = None

    def stop(self):
        """Stop the current timer and save record - Issue #3"""
        # Minimal implementation for Issue #1 - just reset without saving
        # Full implementation in Issue #3
        if self.state == TimerState.IDLE:
            raise ValueError("No timer running")

        # Just reset state without saving (Issue #3 will add full functionality)
        self.state = TimerState.IDLE
        self.current_task = None
        self.current_issue = None
        self.current_record = None
        self.pause_time = None
        self.total_paused = timedelta()

    def status(self) -> dict:
        """Get current status - Issue #4"""
        raise NotImplementedError("Issue #4 not completed yet")

    def generate_daily_report(self) -> str:
        """Generate daily report - Issue #4"""
        raise NotImplementedError("Issue #4 not completed yet")

    def generate_weekly_report(self) -> str:
        """Generate weekly report - Issue #4"""
        raise NotImplementedError("Issue #4 not completed yet")


def main():
    """CLI entry point"""
    import argparse
    print("Task Timer CLI - Run tests first")
    print("Issue #1-4 not completed yet")


if __name__ == "__main__":
    main()