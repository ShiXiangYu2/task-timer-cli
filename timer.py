"""Task Timer CLI - Track task execution time"""

import json
import os
from dataclasses import dataclass, asdict
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
        """Start a new timer"""
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
        """Pause the current timer"""
        if self.state != TimerState.RUNNING:
            raise ValueError("No timer running")
        self.state = TimerState.PAUSED
        self.pause_time = datetime.now()

    def resume(self):
        """Resume a paused timer"""
        if self.state != TimerState.PAUSED:
            raise ValueError("Timer is not paused")
        if self.pause_time:
            self.total_paused += datetime.now() - self.pause_time
        self.state = TimerState.RUNNING
        self.pause_time = None

    def stop(self):
        """Stop the current timer and save record"""
        if self.state == TimerState.IDLE:
            raise ValueError("No timer running")

        if self.current_record:
            self.current_record.end_time = datetime.now()
            self.current_record.paused_duration = self.total_paused
            self.records.append(self.current_record)
            self._save_records()

        self.state = TimerState.IDLE
        self.current_task = None
        self.current_issue = None
        self.current_record = None
        self.pause_time = None
        self.total_paused = timedelta()

    def status(self) -> dict:
        """Get current status"""
        if self.state == TimerState.IDLE:
            return {"state": "idle"}

        elapsed = 0
        if self.current_record:
            elapsed = int((datetime.now() - self.current_record.start_time).total_seconds())
            elapsed -= int(self.total_paused.total_seconds())
            if self.state == TimerState.PAUSED and self.pause_time:
                elapsed -= int((datetime.now() - self.pause_time).total_seconds())

        return {
            "state": self.state.value,
            "task": self.current_task,
            "issue": self.current_issue,
            "elapsed_seconds": elapsed
        }

    def generate_daily_report(self) -> str:
        """Generate daily report"""
        today = datetime.now().date()
        today_records = [
            r for r in self.records
            if r.start_time.date() == today
        ]
        return self._format_report("Daily Report", today_records)

    def generate_weekly_report(self) -> str:
        """Generate weekly report"""
        today = datetime.now()
        week_ago = today - timedelta(days=7)
        week_records = [
            r for r in self.records
            if week_ago <= r.start_time <= today
        ]
        return self._format_report("Weekly Report", week_records)

    def _format_report(self, title: str, records: list[Record]) -> str:
        """Format report from records"""
        lines = [f"# {title} - {datetime.now().strftime('%Y-%m-%d')}", ""]

        if not records:
            lines.append("*No records*")
            return "\n".join(lines)

        total_seconds = sum(r.duration_seconds for r in records)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        lines.append(f"**Total time**: {hours}h {minutes}m")
        lines.append("")
        lines.append("## Tasks")
        lines.append("")

        for r in sorted(records, key=lambda x: x.start_time):
            duration = r.duration_seconds
            h, m = divmod(duration // 60, 60)
            issue_str = f" (#{r.issue_id})" if r.issue_id else ""
            lines.append(f"- **{r.task}**{issue_str}: {h}h {m}m")

        return "\n".join(lines)


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Task Timer CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # start command
    start_parser = subparsers.add_parser("start", help="Start a timer")
    start_parser.add_argument("task", help="Task name")
    start_parser.add_argument("--issue", help="Issue ID")

    # pause command
    subparsers.add_parser("pause", help="Pause the timer")

    # resume command
    subparsers.add_parser("resume", help="Resume the timer")

    # stop command
    subparsers.add_parser("stop", help="Stop the timer")

    # status command
    subparsers.add_parser("status", help="Show timer status")

    # report command
    report_parser = subparsers.add_parser("report", help="Generate report")
    report_parser.add_argument("period", choices=["today", "week"], help="Report period")

    args = parser.parse_args()
    timer = TaskTimer()

    if args.command == "start":
        timer.start(args.task, args.issue)
        print(f"Started: {args.task}")
        if args.issue:
            print(f"Issue: #{args.issue}")

    elif args.command == "pause":
        timer.pause()
        print("Paused")

    elif args.command == "resume":
        timer.resume()
        print("Resumed")

    elif args.command == "stop":
        timer.stop()
        print("Stopped")

    elif args.command == "status":
        status = timer.status()
        if status["state"] == "idle":
            print("No timer running")
        else:
            elapsed = status["elapsed_seconds"]
            h, m, s = elapsed // 3600, (elapsed % 3600) // 60, elapsed % 60
            print(f"{status['task']}: {h:02d}:{m:02d}:{s:02d}")

    elif args.command == "report":
        if args.period == "today":
            print(timer.generate_daily_report())
        else:
            print(timer.generate_weekly_report())


if __name__ == "__main__":
    main()