# CS-499 Milestone Four - Databases
# Thermostat Database
#
# Stores thermostat readings and settings changes in a local
# SQLite database for historical tracking and retrieval.

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from math import isfinite


class ThermostatDatabase:
    """Manage persistent thermostat data in a local SQLite database."""

    def __init__(self, database_path="thermostat.db"):
        self.database_path = str(database_path)
        self.initialize_database()

    @contextmanager
    def _connect(self):
        """Open a connection, commit successful work, and always close it."""
        connection = sqlite3.connect(self.database_path, timeout=5)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize_database(self):
        """Create the database tables if they do not already exist."""
        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS temperature_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    temperature_f REAL NOT NULL
                        CHECK (temperature_f BETWEEN 32 AND 120),
                    mode TEXT NOT NULL
                        CHECK (mode IN ('off', 'heat', 'cool')),
                    setpoint INTEGER NOT NULL
                        CHECK (setpoint BETWEEN 50 AND 90)
                )
            """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS thermostat_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL
                        CHECK (event_type IN ('mode', 'setpoint')),
                    previous_value TEXT NOT NULL,
                    new_value TEXT NOT NULL
                )
            """)
            connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_readings_timestamp
                ON temperature_readings (timestamp)
            """)

    def save_temperature_reading(self, temperature_f, mode, setpoint):
        """Save a validated temperature reading and thermostat settings."""

        # Validate the temperature before saving it to the database.
        if (isinstance(temperature_f, bool)
                or not isinstance(temperature_f, (int, float))
                or not isfinite(temperature_f)
                or not 32 <= temperature_f <= 120):
            raise ValueError("Temperature must be between 32 and 120 F.")

        # Make sure the operating mode and setpoint are valid.
        if mode not in ("off", "heat", "cool"):
            raise ValueError("Invalid thermostat mode.")

        if (isinstance(setpoint, bool)
                or not isinstance(setpoint, int)
                or not 50 <= setpoint <= 90):
            raise ValueError("Setpoint must be between 50 and 90 F.")

        # Record the current time in UTC for consistent history queries.
        timestamp = datetime.now(timezone.utc).isoformat(timespec="auto")

        # Use a parameterized query to safely insert the reading.
        with self._connect() as connection:
            connection.execute("""
                INSERT INTO temperature_readings
                    (timestamp, temperature_f, mode, setpoint)
                VALUES (?, ?, ?, ?)
            """, (timestamp, temperature_f, mode, setpoint))

    def save_setting_change(self, event_type, previous_value, new_value):
        """Save a validated change to the thermostat settings."""

        # Check the event type and validate the previous and new values.
        if event_type == "mode":
            valid_modes = ("off", "heat", "cool")
            if previous_value not in valid_modes or new_value not in valid_modes:
                raise ValueError("Invalid thermostat mode.")

        elif event_type == "setpoint":
            for value in (previous_value, new_value):
                if (type(value) is not int
                        or not 50 <= value <= 90):
                    raise ValueError("Setpoint must be between 50 and 90 F.")

        else:
            raise ValueError("Invalid thermostat event type.")

        # Do not create a history record if the setting has not changed.
        if previous_value == new_value:
            return False

        # Record when the setting was changed using UTC time.
        timestamp = datetime.now(timezone.utc).isoformat(timespec="auto")

        # Save the setting change using a parameterized SQL query.
        with self._connect() as connection:
            connection.execute("""
                INSERT INTO thermostat_events
                    (timestamp, event_type, previous_value, new_value)
                VALUES (?, ?, ?, ?)
            """, (timestamp, event_type, str(previous_value), str(new_value)))

        return True

    def get_temperature_history(self, start_time=None, end_time=None):
        """Retrieve temperature readings, optionally filtered by date."""

        # Validate the requested date range before running the query.
        for value in (start_time, end_time):
            if value is not None:
                if (not isinstance(value, datetime)
                        or value.tzinfo is None
                        or value.utcoffset() is None):
                    raise ValueError("Dates must include timezone information.")

        if start_time and end_time and start_time > end_time:
            raise ValueError("Start time cannot be after end time.")

        # Build the query with optional date filters.
        # Use parameters to safely handle the requested dates.
        query = """
            SELECT id, timestamp, temperature_f, mode, setpoint
            FROM temperature_readings
            WHERE 1 = 1
        """
        parameters = []


        if start_time is not None:
            query += " AND timestamp >= ?"
            parameters.append(
                start_time.astimezone(timezone.utc).isoformat(timespec="auto")
            )

        if end_time is not None:
            query += " AND timestamp <= ?"
            parameters.append(
                end_time.astimezone(timezone.utc).isoformat(timespec="auto")
            )


        # Retrieve records in chronological order.
        query += " ORDER BY timestamp ASC, id ASC"

        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()

        return [dict(row) for row in rows]

    def get_temperature_statistics(self, start_time=None, end_time=None):
        """Calculate temperature statistics for a selected time period."""

        # Validate the requested date range before running the query.
        for value in (start_time, end_time):
            if value is not None:
                if (not isinstance(value, datetime)
                        or value.tzinfo is None
                        or value.utcoffset() is None):
                    raise ValueError("Dates must include timezone information.")

        if start_time and end_time and start_time > end_time:
            raise ValueError("Start time cannot be after end time.")

        # Use SQL aggregate functions to calculate temperature statistics.
        query = """
            SELECT
                COUNT(*) AS reading_count,
                MIN(temperature_f) AS minimum_f,
                MAX(temperature_f) AS maximum_f,
                ROUND(AVG(temperature_f), 2) AS average_f
            FROM temperature_readings
            WHERE 1 = 1
        """
        parameters = []

        # Apply optional start and end dates using parameterized queries.
        if start_time is not None:
            query += " AND timestamp >= ?"
            parameters.append(
                start_time.astimezone(timezone.utc).isoformat(timespec="auto")
            )

        if end_time is not None:
            query += " AND timestamp <= ?"
            parameters.append(
                end_time.astimezone(timezone.utc).isoformat(timespec="auto")
            )
        # Return the calculated values as a dictionary.
        with self._connect() as connection:
            result = connection.execute(query, parameters).fetchone()

        return dict(result)

