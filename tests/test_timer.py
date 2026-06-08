"""Test Task Timer CLI - TDD approach"""

import json
import os
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from timer import TaskTimer, TimerState, Record


class TestTaskTimer:
    """Test TaskTimer class"""

    def setup_method(self):
        """Create temp directory for test data"""
        self.temp_dir = tempfile.mkdtemp()
        self.timer = TaskTimer(data_dir=self.temp_dir)

    def test_start_timer(self):
        """Test starting a new timer"""
        self.timer.start("test task", issue_id="123")
        assert self.timer.state == TimerState.RUNNING
        assert self.timer.current_task == "test task"
        assert self.timer.current_issue == "123"

    def test_pause_timer(self):
        """Test pausing a running timer"""
        self.timer.start("test task")
        self.timer.pause()
        assert self.timer.state == TimerState.PAUSED

    def test_resume_timer(self):
        """Test resuming a paused timer"""
        self.timer.start("test task")
        self.timer.pause()
        self.timer.resume()
        assert self.timer.state == TimerState.RUNNING

    def test_stop_timer(self):
        """Test stopping timer creates a record"""
        self.timer.start("test task")
        self.timer.stop()
        assert self.timer.state == TimerState.IDLE
        assert len(self.timer.records) == 1
        assert self.timer.records[0].task == "test task"

    def test_stop_without_start(self):
        """Test stopping without start raises error"""
        with pytest.raises(ValueError, match="No timer running"):
            self.timer.stop()

    def test_pause_without_start(self):
        """Test pausing without start raises error"""
        with pytest.raises(ValueError, match="No timer running"):
            self.timer.pause()

    def test_multiple_starts(self):
        """Test starting new timer without stopping previous"""
        self.timer.start("task 1")
        self.timer.start("task 2")  # Should stop task 1
        assert self.timer.current_task == "task 2"


class TestRecordSerialization:
    """Test Record serialization to/from JSON"""

    def test_record_to_dict(self):
        """Test Record to dict conversion"""
        start = datetime(2024, 1, 1, 10, 0, 0)
        end = datetime(2024, 1, 1, 11, 0, 0)
        record = Record(
            task="test task",
            issue_id="123",
            start_time=start,
            end_time=end
        )
        data = record.to_dict()
        assert data["task"] == "test task"
        assert data["issue_id"] == "123"
        # duration_seconds is a property, not stored in dict
        assert record.duration_seconds == 3600

    def test_record_from_dict(self):
        """Test Record from dict"""
        data = {
            "task": "test task",
            "issue_id": "456",
            "start_time": "2024-01-01T10:00:00",
            "end_time": "2024-01-01T10:30:00"
        }
        record = Record.from_dict(data)
        assert record.task == "test task"
        assert record.issue_id == "456"
        assert record.duration_seconds == 1800


class TestReportGeneration:
    """Test report generation"""

    def setup_method(self):
        """Create timer with test data"""
        self.temp_dir = tempfile.mkdtemp()
        self.timer = TaskTimer(data_dir=self.temp_dir)

    def test_daily_report(self):
        """Test generating daily report"""
        # Create a record for today
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        self.timer.records = [
            Record(
                task="yesterday task",
                start_time=yesterday.replace(hour=10),
                end_time=yesterday.replace(hour=11)
            ),
            Record(
                task="today task",
                start_time=today.replace(hour=10),
                end_time=today.replace(hour=11)
            )
        ]
        report = self.timer.generate_daily_report()
        assert "today task" in report
        assert "yesterday task" not in report

    def test_weekly_report(self):
        """Test generating weekly report"""
        today = datetime.now()
        last_week = today - timedelta(days=7)
        self.timer.records = [
            Record(
                task="last week task",
                start_time=last_week,
                end_time=last_week + timedelta(hours=1)
            ),
            Record(
                task="this week task",
                start_time=today - timedelta(days=1),
                end_time=today - timedelta(days=1) + timedelta(hours=2)
            )
        ]
        report = self.timer.generate_weekly_report()
        assert "this week task" in report
        assert "last week task" not in report