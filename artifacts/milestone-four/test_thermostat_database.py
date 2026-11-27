# CS-499 Milestone Four - Databases
# Automated Thermostat Database Tests
#
# Tests local SQLite storage, retrieval, validation, and data integrity
# without requiring Raspberry Pi hardware.

import sqlite3
import tempfile
from contextlib import closing
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from thermostat_database import ThermostatDatabase


class TestThermostatDatabase(unittest.TestCase):
    """Verify thermostat database operations using temporary files."""

    def setUp(self):
        """Create a separate SQLite database before each test."""

        # Keep test records out of the actual thermostat database.
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_directory.name) / "test_thermostat.db"
        self.database = ThermostatDatabase(self.database_path)

    def tearDown(self):
        """Remove temporary database files after each test."""
        self.temp_directory.cleanup()

    def test_database_initialization(self):
        """Verify both tables are created and initialization is repeatable."""

        # Opening the same database again should preserve its tables.
        ThermostatDatabase(self.database_path)
        with closing(sqlite3.connect(self.database_path)) as connection:
            rows = connection.execute("""
                SELECT name FROM sqlite_master
                WHERE type = 'table'
                AND name IN ('temperature_readings', 'thermostat_events')
                ORDER BY name
            """).fetchall()

        self.assertEqual(rows, [
            ("temperature_readings",), ("thermostat_events",)
        ])

    def test_save_and_retrieve_reading(self):
        """Verify a saved reading can be retrieved after reopening."""

        self.database.save_temperature_reading(72.5, "heat", 70)

        # A second database instance should find the persisted record.
        reopened = ThermostatDatabase(self.database_path)
        readings = reopened.get_temperature_history()
        self.assertEqual(len(readings), 1)
        self.assertEqual(readings[0]["temperature_f"], 72.5)
        self.assertEqual(readings[0]["mode"], "heat")
        self.assertEqual(readings[0]["setpoint"], 70)
        self.assertIsNotNone(readings[0]["timestamp"])

    def test_temperature_statistics(self):
        """Verify SQL calculates the correct count, minimum, maximum, and average."""

        for temperature in (72.5, 65.0, 78.0, 71.5):
            self.database.save_temperature_reading(temperature, "off", 72)

        self.assertEqual(self.database.get_temperature_statistics(), {
            "reading_count": 4,
            "minimum_f": 65.0,
            "maximum_f": 78.0,
            "average_f": 71.75
        })

    def test_empty_temperature_statistics(self):
        """Verify empty databases return no temperature statistics."""

        self.assertEqual(self.database.get_temperature_statistics(), {
            "reading_count": 0,
            "minimum_f": None,
            "maximum_f": None,
            "average_f": None
        })

    def test_history_date_filtering(self):
        """Verify date filters select only readings within the requested period."""

        # Use known dates so the query must exclude older and newer records.
        readings = [
            ("2026-11-24T12:00:00+00:00", 65.0, "heat", 70),
            ("2026-11-25T12:00:00+00:00", 72.0, "off", 72),
            ("2026-11-26T12:00:00+00:00", 78.0, "cool", 72)
        ]
        with closing(sqlite3.connect(self.database_path)) as connection:
            connection.executemany("""
                INSERT INTO temperature_readings
                    (timestamp, temperature_f, mode, setpoint)
                VALUES (?, ?, ?, ?)
            """, readings)
            connection.commit()

        # Only the November 25 reading should fall inside this range.
        start = datetime(2026, 11, 25, tzinfo=timezone.utc)
        end = datetime(2026, 11, 26, tzinfo=timezone.utc)
        matching = self.database.get_temperature_history(start, end)
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["temperature_f"], 72.0)

        # Statistics should use the same date filters.
        statistics = self.database.get_temperature_statistics(start, end)
        self.assertEqual(statistics["reading_count"], 1)
        self.assertEqual(statistics["average_f"], 72.0)

        # A period without records should return no temperature history.
        missing = self.database.get_temperature_history(
            datetime(2026, 11, 21, tzinfo=timezone.utc),
            datetime(2026, 11, 22, tzinfo=timezone.utc)
        )
        self.assertEqual(missing, [])

    def test_fractional_second_filtering(self):
        """Verify date filters handle readings within the same second."""

        # Include an older timestamp without fractional seconds.
        readings = [
            ("2026-11-25T12:00:00+00:00", 65.0, "heat", 70),
            ("2026-11-25T12:00:00.250000+00:00", 72.0, "off", 72),
            ("2026-11-25T12:00:00.750000+00:00", 78.0, "cool", 72)
        ]

        with closing(sqlite3.connect(self.database_path)) as connection:
            connection.executemany("""
                INSERT INTO temperature_readings
                    (timestamp, temperature_f, mode, setpoint)
                VALUES (?, ?, ?, ?)
            """, readings)
            connection.commit()

        # Select only the reading recorded at 250 milliseconds.
        start = datetime(2026, 11, 25, 12, 0, 0, 200000,
                         tzinfo=timezone.utc)
        end = datetime(2026, 11, 25, 12, 0, 0, 500000,
                       tzinfo=timezone.utc)

        matching = self.database.get_temperature_history(start, end)

        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["temperature_f"], 72.0)

        # Verify the statistics use the same precise date range.
        statistics = self.database.get_temperature_statistics(start, end)
        self.assertEqual(statistics["reading_count"], 1)
        self.assertEqual(statistics["average_f"], 72.0)

    def test_statistics_date_filtering(self):
        """Verify statistics include only records within the date range."""

        self.database.save_temperature_reading(74.0, "cool", 72)
        now = datetime.now(timezone.utc)
        result = self.database.get_temperature_statistics(
            now - timedelta(days=1), now + timedelta(days=1)
        )
        self.assertEqual(result["reading_count"], 1)
        self.assertEqual(result["average_f"], 74.0)

        missing = self.database.get_temperature_statistics(
            datetime(2020, 1, 1, tzinfo=timezone.utc),
            datetime(2020, 1, 2, tzinfo=timezone.utc)
        )
        self.assertEqual(missing["reading_count"], 0)

    def test_invalid_temperature_values(self):
        """Verify invalid temperature readings are not saved."""

        # Reject out-of-range, missing, nonnumeric, and non-finite values.
        invalid_values = (-10, 121, None, "72", True,
                          float("nan"), float("inf"))
        for value in invalid_values:
            with self.subTest(temperature=value):
                with self.assertRaises(ValueError):
                    self.database.save_temperature_reading(value, "heat", 70)

        self.assertEqual(self.database.get_temperature_history(), [])

    def test_invalid_mode_and_setpoint(self):
        """Verify invalid thermostat settings cannot be saved."""

        for mode in ("fan", "HEAT", None):
            with self.subTest(mode=mode):
                with self.assertRaises(ValueError):
                    self.database.save_temperature_reading(72, mode, 70)

        for setpoint in (49, 91, True, "72"):
            with self.subTest(setpoint=setpoint):
                with self.assertRaises(ValueError):
                    self.database.save_temperature_reading(72, "heat", setpoint)

        self.assertEqual(self.database.get_temperature_history(), [])

    def test_save_setting_changes(self):
        """Verify operating mode and setpoint changes are recorded."""

        self.assertTrue(self.database.save_setting_change("mode", "off", "heat"))
        self.assertTrue(self.database.save_setting_change("setpoint", 72, 73))

        with closing(sqlite3.connect(self.database_path)) as connection:
            events = connection.execute("""
                SELECT event_type, previous_value, new_value
                FROM thermostat_events ORDER BY id
            """).fetchall()

        self.assertEqual(events, [
            ("mode", "off", "heat"),
            ("setpoint", "72", "73")
        ])

    def test_unchanged_settings_are_not_saved(self):
        """Verify duplicate setting values do not create events."""

        self.assertFalse(self.database.save_setting_change("mode", "off", "off"))
        self.assertFalse(self.database.save_setting_change("setpoint", 72, 72))

        with closing(sqlite3.connect(self.database_path)) as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM thermostat_events"
            ).fetchone()[0]
        self.assertEqual(count, 0)

    def test_invalid_setting_changes(self):
        """Verify invalid event types and setting values are rejected."""

        for values in (("fan", "off", "heat"),
                       ("mode", "off", "fan"),
                       ("setpoint", 72, 95),
                       ("setpoint", True, 72)):
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    self.database.save_setting_change(*values)

    def test_invalid_date_ranges(self):
        """Verify date filters reject naive or reversed timestamps."""

        naive = datetime(2026, 1, 1)
        start = datetime(2026, 1, 2, tzinfo=timezone.utc)
        end = datetime(2026, 1, 1, tzinfo=timezone.utc)

        for method in (self.database.get_temperature_history,
                       self.database.get_temperature_statistics):
            with self.subTest(method=method.__name__):
                with self.assertRaises(ValueError):
                    method(start_time=naive)
                with self.assertRaises(ValueError):
                    method(start_time=start, end_time=end)

    def test_database_constraints(self):
        """Verify SQLite rejects invalid records even without Python checks."""

        # Database CHECK constraints provide a second layer of validation.
        with closing(sqlite3.connect(self.database_path)) as connection:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("""
                    INSERT INTO temperature_readings
                        (timestamp, temperature_f, mode, setpoint)
                    VALUES (?, ?, ?, ?)
                """, ("2026-01-01T00:00:00+00:00", 72, "fan", 72))


if __name__ == "__main__":
    # Run all tests when this file is executed directly.
    unittest.main()
