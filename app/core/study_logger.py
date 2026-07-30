import csv
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class UsabilityStudyLogger:
    """
    A local, telemetry-free logger for usability studies.
    
    Requirements satisfied:
    - Does not send data to any server.
    - Requires explicit participant consent to enable logging.
    - Generates a pseudonymous participant ID.
    - Records task events, durations, and error counts.
    - Does not record actual image contents or sensitive paths.
    - Supports exporting recorded data to CSV.
    - Can be disabled at any time.
    """

    def __init__(self, log_dir: str = "study_logs"):
        self.enabled = False
        self.consent_given = False
        self.participant_id: Optional[str] = None
        self.log_dir = Path(log_dir)
        self.current_task: Optional[str] = None
        self.task_start_time: Optional[float] = None
        self.events: list[Dict[str, Any]] = []

    def enable(self, consent_given: bool):
        """Enable logging if consent is given. Generates a new pseudonymous ID."""
        if consent_given:
            self.consent_given = True
            self.enabled = True
            self.participant_id = str(uuid.uuid4())
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.log_event("study_started", {})
        else:
            self.disable()

    def disable(self):
        """Disable logging completely."""
        self.enabled = False
        self.consent_given = False
        self.participant_id = None

    def start_task(self, task_name: str):
        """Mark the beginning of a specific task."""
        if not self.enabled:
            return

        self.current_task = task_name
        self.task_start_time = time.time()
        self.log_event("task_started", {"task_name": task_name})

    def end_task(self, task_name: str, success: bool, error_count: int = 0):
        """Mark the end of a specific task and record its duration."""
        if not self.enabled or self.current_task != task_name:
            return

        duration = time.time() - self.task_start_time if self.task_start_time else 0.0

        self.log_event("task_ended", {
            "task_name": task_name,
            "success": success,
            "duration_seconds": round(duration, 2),
            "error_count": error_count
        })

        self.current_task = None
        self.task_start_time = None

    def log_error(self, error_type: str, context: str = ""):
        """Log an error occurrence without recording sensitive data."""
        if not self.enabled:
            return

        self.log_event("error_occurred", {
            "task_name": self.current_task,
            "error_type": error_type,
            "context": context
        })

    def log_event(self, event_type: str, details: Dict[str, Any]):
        """Record a generic event."""
        if not self.enabled:
            return

        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "participant_id": self.participant_id,
            "event_type": event_type,
            **details
        }
        self.events.append(event)

    def export_csv(self, filename: Optional[str] = None) -> Optional[str]:
        """Export all recorded events to a local CSV file."""
        if not self.events:
            return None

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"study_log_{timestamp}.csv"

        filepath = self.log_dir / filename

        # Determine all possible columns from events
        fieldnames = ["timestamp", "participant_id", "event_type", "task_name", "success", "duration_seconds", "error_count", "error_type", "context"]

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for event in self.events:
                writer.writerow(event)

        return str(filepath)


# Global default instance for the application to use
study_logger = UsabilityStudyLogger()
