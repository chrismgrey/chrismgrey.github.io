# CS-499 Milestone Three - Algorithms and Data Structures
# Hardware Integration Tests
#
# Tests the Raspberry Pi thermostat's temperature sampling and
# caching behavior without requiring physical hardware.
#
# Simulated hardware components allow us to verify that multiple
# temperature requests do not create unnecessary sensor readings.

import unittest

# Read the hardware-facing Python code without initializing the Raspberry Pi.
import ast
from pathlib import Path

# Use a threading lock to simulate synchronized sensor access.
from threading import Lock

from unittest.mock import Mock, patch, PropertyMock

# Use the actual thermostat controller to verify temperature processing.
from thermostat_core import ThermostatCore

def load_hardware_source():
    """Read the Raspberry Pi application without running it."""
    
    # Locate enhanced.py in the same folder as this test file
    # so the tests work without a hardcoded file path.
    source_path = Path(__file__).with_name("enhanced.py")

    # Parse the Python code without initializing the hardware.
    return ast.parse(source_path.read_text(encoding="utf-8"))

def get_temperature_machine_node():
    """Locate the thermostat hardware-management class."""

    # Search the parsed source for the TemperatureMachine class
    # so we can test its methods without starting the hardware.
    tree = load_hardware_source()

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "TemperatureMachine":
            return node

    # Report an error if the expected class cannot be found.
    raise ValueError("TemperatureMachine class not found in enhanced.py.")

def get_sensor_method_node():
    """Locate the hardware temperature-reading method."""

    # Find getFahrenheit inside TemperatureMachine so we can
    # test the actual sensor-processing code without hardware.
    class_node = get_temperature_machine_node()

    for node in class_node.body:
        if isinstance(node, ast.FunctionDef) and node.name == "getFahrenheit":
            return node

    # Raise an error if the expected sensor method is missing.
    raise ValueError("getFahrenheit method not found in TemperatureMachine.")

def load_sensor_method():
    """Load the temperature-reading method for isolated testing."""

    # Extract the actual sensor method into a temporary module
    # so it can be tested without starting the Raspberry Pi.
    method_node = get_sensor_method_node()
    test_module = ast.Module(body=[method_node], type_ignores=[])
    ast.fix_missing_locations(test_module)

    # Compile the isolated method without running any hardware code.
    namespace = {}
    exec(compile(test_module, "enhanced.py", "exec"), namespace)

    return namespace["getFahrenheit"]

def configure_sensor_method(method, sensor, clock):
    """Supply simulated hardware dependencies to the sensor method."""

    # Provide the same sensor lock used by the hardware application
    # while replacing the physical sensor and timer with test objects.
    method.__globals__["sensorLock"] = Lock()
    method.__globals__["thSensor"] = sensor
    method.__globals__["monotonic"] = clock
    method.__globals__["ThermostatCore"] = ThermostatCore

    return method

class TestHardwareIntegration(unittest.TestCase):
    """Verify temperature processing in the hardware application."""

    def setUp(self):
        """Prepare simulated hardware before each test."""

        # Load the actual sensor method and simulate a normal
        # temperature reading of 20 degrees Celsius.
        self.method = load_sensor_method()
        self.sensor = Mock(temperature=20.0)
        self.clock = Mock(return_value=10.0)

        # Connect the simulated sensor and timer to the method.
        configure_sensor_method(self.method, self.sensor, self.clock)

        # Create a thermostat controller with an empty cache
        # to match the initial state of the hardware application.
        self.machine = Mock()
        self.machine.core = ThermostatCore()
        self.machine.cached_temperature_f = None
        self.machine.last_sample_time = None
        self.machine.SAMPLE_INTERVAL_SECONDS = 1.0

    def test_cached_reading_is_reused(self):
        """Verify repeated requests reuse the cached temperature."""

        # Request the temperature twice without advancing the clock
        # to simulate multiple hardware functions requesting data.
        first_temperature = self.method(self.machine)
        second_temperature = self.method(self.machine)

        # Confirm both requests return the same processed temperature.
        self.assertAlmostEqual(first_temperature, 68.0)
        self.assertAlmostEqual(second_temperature, 68.0)

        # Verify only one reading entered the temperature history
        # because the second request reused the cached value.
        self.assertEqual(
            list(self.machine.core.temperature_history.readings),
            [68.0]
        )

        # Confirm the cache recorded the simulated sample time.
        self.assertEqual(self.machine.last_sample_time, 10.0)

    def test_new_reading_after_interval(self):
        """Verify a new sensor reading is processed after the interval."""

        # Collect the first temperature reading at the starting time.
        first_temperature = self.method(self.machine)

        # Simulate the room warming up and advance the clock
        # beyond the one-second sampling interval.
        self.sensor.temperature = 22.0
        self.clock.return_value = 11.1

        # Request another reading after the cached value expires.
        second_temperature = self.method(self.machine)

        # Confirm the first reading was 68 F and the updated
        # rolling average correctly includes the new 71.6 F reading.
        self.assertAlmostEqual(first_temperature, 68.0)
        self.assertAlmostEqual(second_temperature, 69.8)

        # Verify both accepted readings are stored in the queue
        # rather than reusing the old cached temperature.
        self.assertEqual(
            len(self.machine.core.temperature_history.readings), 2
        )
        self.assertAlmostEqual(self.machine.last_sample_time, 11.1)

    def test_invalid_sensor_reading(self):
        """Verify invalid sensor data does not affect temperature history."""

        # Collect a valid reading to establish the starting
        # temperature history and cached value.
        self.method(self.machine)

        # Simulate an invalid sensor reading after the
        # previous cached temperature has expired.
        self.sensor.temperature = float("nan")
        self.clock.return_value = 11.1

        # Confirm the invalid reading is rejected rather
        # than being used for temperature calculations.
        with self.assertRaises(ValueError):
            self.method(self.machine)

        # Verify the invalid reading did not change the
        # accepted temperature history or cached value.
        self.assertEqual(
            list(self.machine.core.temperature_history.readings),
            [68.0]
        )
        self.assertAlmostEqual(self.machine.cached_temperature_f, 68.0)
        self.assertEqual(self.machine.last_sample_time, 10.0)

    def test_recovery_after_invalid_reading(self):
        """Verify the thermostat resumes processing after invalid sensor data."""

        # Establish a valid starting temperature and cached value.
        self.method(self.machine)

        # Simulate an invalid sensor reading after the cache expires.
        self.sensor.temperature = float("nan")
        self.clock.return_value = 11.1

        # Confirm the invalid reading is rejected without stopping
        # the temperature-processing algorithm.
        with self.assertRaises(ValueError):
            self.method(self.machine)

        # Restore a valid sensor temperature and advance the clock
        # so the thermostat can collect another reading.
        self.sensor.temperature = 22.0
        self.clock.return_value = 12.2

        recovered_temperature = self.method(self.machine)

        # Verify the new reading is accepted and averaged
        # with the previously stored valid temperature.
        self.assertAlmostEqual(recovered_temperature, 69.8)
        self.assertEqual(
            len(self.machine.core.temperature_history.readings), 2
        )

        # Confirm the cache and timestamp are updated after recovery.
        self.assertAlmostEqual(self.machine.cached_temperature_f, 69.8)
        self.assertAlmostEqual(self.machine.last_sample_time, 12.2)

        
    def test_hardware_temperature_spike(self):
        """Verify an unusual sensor reading does not affect the average."""

        # Collect three normal readings to establish a temperature
        # baseline before testing the abnormal reading threshold.
        for sample_time in [10.0, 11.1, 12.2]:
            self.clock.return_value = sample_time
            self.method(self.machine)

        # Simulate a sudden temperature spike after the cache
        # expires so the thermostat processes a new sensor reading.
        self.sensor.temperature = 36.0
        self.clock.return_value = 13.3

        processed_temperature = self.method(self.machine)

        # Verify the unusual reading is flagged without changing
        # the previously established rolling average.
        self.assertEqual(
            self.machine.core.temperature_history.last_status,
            "flagged"
        )
        self.assertAlmostEqual(processed_temperature, 68.0)

        # Confirm the abnormal reading was excluded from the queue
        # and the cached processed temperature remains stable.
        self.assertEqual(
            list(self.machine.core.temperature_history.readings),
            [68.0, 68.0, 68.0]
        )
        self.assertAlmostEqual(self.machine.cached_temperature_f, 68.0)


    def test_hardware_confirmed_temperature_change(self):
        """Verify consecutive unusual readings establish a new baseline."""

        # Collect three normal readings to establish the
        # initial temperature history at 68 degrees Fahrenheit.
        for sample_time in [10.0, 11.1, 12.2]:
            self.clock.return_value = sample_time
            self.method(self.machine)

        # Introduce an unusual temperature reading that should
        # be flagged without changing the existing average.
        self.sensor.temperature = 36.0
        self.clock.return_value = 13.3
        self.method(self.machine)

        # Submit a second similar reading after the cache expires
        # to confirm the temperature change is not an isolated spike.
        self.sensor.temperature = 36.5
        self.clock.return_value = 14.4

        processed_temperature = self.method(self.machine)

        # Verify the algorithm recognizes the confirmed change
        # and resets the previous temperature history.
        self.assertEqual(
            self.machine.core.temperature_history.last_status,
            "confirmed_change"
        )
        self.assertEqual(
            len(self.machine.core.temperature_history.readings), 1
        )

        # Confirm the new 97.7 F reading becomes the starting
        # temperature for the updated history and cache.
        self.assertAlmostEqual(processed_temperature, 97.7)
        self.assertAlmostEqual(
            self.machine.cached_temperature_f, 97.7
        )

        # Verify the pending abnormal reading is cleared
        # after the new temperature baseline is established.
        self.assertIsNone(
            self.machine.core.temperature_history.pending_reading
        )


    def test_sensor_communication_failure(self):
        """Verify a sensor communication error preserves valid history."""

        # Collect a valid reading before simulating a sensor failure.
        self.method(self.machine)

        # Advance the clock beyond the cache interval so
        # the thermostat attempts another sensor reading.
        self.clock.return_value = 11.1

        # Simulate a hardware communication error when the
        # thermostat tries to access the sensor temperature.
        with patch.object(
            type(self.sensor), "temperature",
            new_callable=PropertyMock, create=True
        ) as mock_temperature:
            mock_temperature.side_effect = OSError("Sensor communication failed")

            # Confirm the hardware error is reported rather
            # than accepting an invalid temperature.
            with self.assertRaises(OSError):
                self.method(self.machine)

        # Verify the failed reading did not modify the
        # previously accepted temperature history.
        self.assertEqual(
            list(self.machine.core.temperature_history.readings),
            [68.0]
        )

        # Confirm the cached temperature and timestamp remain
        # unchanged after the unsuccessful sensor request.
        self.assertAlmostEqual(self.machine.cached_temperature_f, 68.0)
        self.assertEqual(self.machine.last_sample_time, 10.0)


