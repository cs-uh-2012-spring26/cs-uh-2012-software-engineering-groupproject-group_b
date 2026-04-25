from abc import ABC, abstractmethod
from datetime import date, timedelta
from typing import Iterator


class RecurrenceStrategy(ABC):
    @abstractmethod
    def generate_dates(self, start: date, end: date) -> Iterator[date]:
        """Yield each occurrence date from start to end, inclusive."""


class DailyRecurrence(RecurrenceStrategy):
    def generate_dates(self, start: date, end: date) -> Iterator[date]:
        current = start
        while current <= end:
            yield current
            current += timedelta(days=1)


class WeeklyRecurrence(RecurrenceStrategy):
    def generate_dates(self, start: date, end: date) -> Iterator[date]:
        current = start
        while current <= end:
            yield current
            current += timedelta(weeks=1)


_STRATEGIES: dict[str, RecurrenceStrategy] = {
    "daily": DailyRecurrence(),
    "weekly": WeeklyRecurrence(),
}

SUPPORTED_RECURRENCES: list[str] = list(_STRATEGIES.keys())


def get_recurrence_strategy(recurrence_type: str) -> RecurrenceStrategy | None:
    """Return the strategy for the given type, or None if unsupported."""
    return _STRATEGIES.get(recurrence_type.lower())
