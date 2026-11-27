# CS-499 Milestone Four - Databases
# Hardware Database Integration Tests
#
# Tests SQLite recording in the Raspberry Pi thermostat without
# connecting physical hardware or modifying the main database.

import ast
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from threading import Lock
from unittest.mock import Mock

from thermostat_core import ThermostatCore
from thermostat_database import ThermostatDatabase


def load_database_hardware_methods():
    """Load the actual hardware methods without starting the Raspberry Pi."""

    # Extract only the methods needed to test SQLite integration.
    source_path = Path(__file__).with_name("enhanced.py")
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    class_node = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "TemperatureMachine"
    )

    selected_names = {
        "recordSettingChange", "recordTemperatureReading", "getFahrenheit",
        "processTempStateButton", "processTempIncButton", "processTempDecButton"
    }
    selected_methods = [
        node for node in class_node.body
        if isinstance(node, ast.FunctionDef) and node.name in selected_names
    ]

    # Compile the original method bodies with simulated dependencies.
    test_class = ast.ClassDef(
        name="TestTemperatureMachine", bases=[], keywords=[],
        body=selected_methods, decorator_list=[]
    )
    module = ast.fix_missing_locations(
        ast.Module(body=[test_class], type_ignores=[])
    )

    namespace = {
        "DEBUG": False,
        "sqlite3": sqlite3,
        "ThermostatCore": ThermostatCore,
        "sensorLock": Lock(),
        "thSensor": Mock(temperature=20.0),
        "monotonic": Mock(return_value=10.0)
    }

    exec(compile(module, str(source_path), "exec"), namespace)
    return namespace["TestTemperatureMachine"], namespace


class TestHardwareDatabaseIntegration(unittest.TestCase):
    """Verify database recording in hardware-facing thermostat methods."""

    def setUp(self):
        """Create a temporary database and simulated sensor before each test."""

        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)

        database_path = Path(self.temporary_directory.name) / "hardware_test.db"
        self.database = ThermostatDatabase(database_path)

        machine_class, self.namespace = load_database_hardware_methods()
        self.machine = machine_class()
        self.machine.core = ThermostatCore()
        self.machine.database = self.database
        self.machine.cached_temperature_f = None
        self.machine.last_sample_time = None
        self.machine.SAMPLE_INTERVAL_SECONDS = 1.0
        self.machine.updateLights = Mock()

        self.sensor = self.namespace["thSensor"]
        self.clock = self.namespace["monotonic"]

    def test_accepted_reading_is_saved(self):
        """Verify a new sensor sample is saved with its thermostat settings."""

        self.machine.getFahrenheit()
        readings = self.database.get_temperature_history()

        self.assertEqual(len(readings), 1)
        self.assertAlmostEqual(readings[0]["temperature_f"], 68.0)
        self.assertEqual(readings[0]["mode"], "off")
        self.assertEqual(readings[0]["setpoint"], 72)

    def test_cached_reading_is_not_saved_again(self):
        """Verify repeat requests do not duplicate an earlier database row."""

        self.machine.getFahrenheit()
        self.machine.getFahrenheit()

        self.assertEqual(len(self.database.get_temperature_history()), 1)
        self.assertEqual(len(self.machine.core.temperature_history.readings), 1)

    def test_new_reading_after_cache_expires(self):
        """Verify a new sensor sample is recorded after the cache expires."""

        self.machine.getFahrenheit()
        self.sensor.temperature = 22.0
        self.clock.return_value = 11.1
        self.machine.getFahrenheit()

        readings = self.database.get_temperature_history()
        self.assertEqual(len(readings), 2)
        self.assertAlmostEqual(readings[1]["temperature_f"], 71.6)

    def test_spike_is_skipped_but_confirmed_change_is_saved(self):
        """Verify abnormal samples are excluded until a change is confirmed."""

        # Establish three readings for the abnormal-temperature baseline.
        for sample_time in (10.0, 11.1, 12.2):
            self.clock.return_value = sample_time
            self.machine.getFahrenheit()

        self.sensor.temperature = 36.0
        self.clock.return_value = 13.3
        self.machine.getFahrenheit()

        self.assertEqual(len(self.database.get_temperature_history()), 3)

        # A second similar reading confirms the temperature change.
        self.sensor.temperature = 36.5
        self.clock.return_value = 14.4
        self.machine.getFahrenheit()

        readings = self.database.get_temperature_history()
        self.assertEqual(len(readings), 4)
        self.assertAlmostEqual(readings[-1]["temperature_f"], 97.7)

    def test_mode_and_setpoint_buttons_record_events(self):
        """Verify physical button callbacks save their setting transitions."""

        self.machine.processTempStateButton()
        self.machine.processTempIncButton()
        self.machine.processTempDecButton()

        # Retrieve the recorded events from the temporary database.
        with closing(sqlite3.connect(self.database.database_path)) as connection:
            events = connection.execute("""
                SELECT event_type, previous_value, new_value
                FROM thermostat_events ORDER BY id
            """).fetchall()

        self.assertEqual(events, [
            ("mode", "off", "heat"),
            ("setpoint", "72", "73"),
            ("setpoint", "73", "72")
        ])
        self.assertEqual(self.machine.updateLights.call_count, 3)

    def test_setpoint_limit_does_not_create_event(self):
        """Verify a button press at the setpoint limit is not recorded."""

        self.machine.core.setpoint = 90
        self.machine.processTempIncButton()

        with closing(sqlite3.connect(self.database.database_path)) as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM thermostat_events"
            ).fetchone()[0]

        self.assertEqual(count, 0)

    def test_database_failure_does_not_stop_hardware_logic(self):
        """Verify SQLite errors do not interrupt sensor or button operations."""

        # Replace storage with a database that raises an SQLite error.
        self.machine.database = Mock()
        self.machine.database.save_temperature_reading.side_effect = (
            sqlite3.OperationalError("database unavailable")
        )
        self.machine.database.save_setting_change.side_effect = (
            sqlite3.OperationalError("database unavailable")
        )

        self.assertAlmostEqual(self.machine.getFahrenheit(), 68.0)
        self.machine.processTempStateButton()

        self.assertEqual(self.machine.core.mode, "heat")
        self.machine.updateLights.assert_called_once()

    def test_database_write_occurs_after_sensor_lock(self):
        """Verify SQLite recording does not hold the sensor-processing lock."""

        self.machine.database = Mock()
        locked_states = []

        self.machine.database.save_temperature_reading.side_effect = (
            lambda *args: locked_states.append(
                self.namespace["sensorLock"].locked()
            )
        )

        self.machine.getFahrenheit()
        self.assertEqual(locked_states, [False])

    def test_setting_changes_saved_after_led_failure(self):
        """Verify LED errors do not prevent setting changes from being saved."""

        # Simulate an LED failure during each physical button operation.
        self.machine.updateLights.side_effect = OSError("LED unavailable")

        # Each button should still save its setting change.
        with self.assertRaises(OSError):
            self.machine.processTempStateButton()

        with self.assertRaises(OSError):
            self.machine.processTempIncButton()

        with self.assertRaises(OSError):
            self.machine.processTempDecButton()

        # Verify all three changes were recorded despite the LED errors.
        with closing(sqlite3.connect(self.database.database_path)) as connection:
            events = connection.execute("""
                SELECT event_type, previous_value, new_value
                FROM thermostat_events ORDER BY id
            """).fetchall()

        self.assertEqual(events, [
            ("mode", "off", "heat"),
            ("setpoint", "72", "73"),
            ("setpoint", "73", "72")
        ])

        # Confirm the LED update was attempted for each button.
        self.assertEqual(self.machine.updateLights.call_count, 3)

if __name__ == "__main__":
    # Run these tests separately if this file is executed directly.
    unittest.main()
