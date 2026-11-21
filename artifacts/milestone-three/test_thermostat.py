# CS-499 Milestone Two - Software Design and Engineering
# Automated Thermostat Tests
#
# Tests the thermostat's core functionality without requiring
# Raspberry Pi hardware.


import unittest
from thermostat_core import ThermostatCore


class TestThermostatCore(unittest.TestCase):
    """Verify thermostat operation and control logic."""

    def setUp(self):
        """Create a fresh thermostat instance before each test."""

        # Start each test with the default thermostat settings.
        self.thermostat = ThermostatCore()

    def test_default_settings(self):
        """Verify the initial operating mode and setpoint."""

        # The thermostat should start in OFF mode at 72 degrees.
        self.assertEqual(self.thermostat.mode, "off")
        self.assertEqual(self.thermostat.setpoint, 72)

    def test_mode_transitions(self):
        """Verify the OFF, HEAT, COOL operating sequence."""

        # Confirm each button cycle advances to the correct mode.
        self.assertEqual(self.thermostat.cycle_mode(), "heat")
        self.assertEqual(self.thermostat.cycle_mode(), "cool")
        self.assertEqual(self.thermostat.cycle_mode(), "off")


    def test_setpoint_adjustments(self):
        """Verify one-degree setpoint increases and decreases."""

        # Confirm the setpoint increases and decreases correctly.
        self.assertEqual(self.thermostat.increase_setpoint(), 73)
        self.assertEqual(self.thermostat.increase_setpoint(), 74)
        self.assertEqual(self.thermostat.decrease_setpoint(), 73)

    def test_setpoint_limits(self):
        """Verify the minimum and maximum setpoint boundaries."""

        # Confirm the setpoint cannot exceed 90 degrees.
        self.thermostat.setpoint = 89
        self.assertEqual(self.thermostat.increase_setpoint(), 90)
        self.assertEqual(self.thermostat.increase_setpoint(), 90)

        # Confirm the setpoint cannot drop below 50 degrees.
        self.thermostat.setpoint = 51
        self.assertEqual(self.thermostat.decrease_setpoint(), 50)
        self.assertEqual(self.thermostat.decrease_setpoint(), 50)

    def test_led_states(self):
        """Verify LED behavior for each thermostat operating mode."""

        # OFF mode should keep both LEDs disabled.
        self.assertEqual(
            self.thermostat.get_led_states(70),
            {"red": "off", "blue": "off"}
        )

        # HEAT mode should pulse below the setpoint and remain
        # solid when the desired temperature is reached.
        self.thermostat.cycle_mode()
        self.assertEqual(
            self.thermostat.get_led_states(68),
            {"red": "pulse", "blue": "off"}
        )
        self.assertEqual(
            self.thermostat.get_led_states(72),
            {"red": "on", "blue": "off"}
        )

        # COOL mode should pulse above the setpoint and remain
        # solid when the desired temperature is reached.
        self.thermostat.cycle_mode()
        self.assertEqual(
            self.thermostat.get_led_states(78),
            {"red": "off", "blue": "pulse"}
        )
        self.assertEqual(
            self.thermostat.get_led_states(72),
            {"red": "off", "blue": "on"}
        )

    def test_temperature_conversion(self):
        """Verify accurate Celsius-to-Fahrenheit conversion."""

        # Confirm common Celsius readings convert correctly.
        self.assertEqual(
            self.thermostat.celsius_to_fahrenheit(0), 32.0
        )
        self.assertEqual(
            self.thermostat.celsius_to_fahrenheit(20), 68.0
        )
        self.assertEqual(
            self.thermostat.celsius_to_fahrenheit(25), 77.0
        )
        self.assertEqual(
            self.thermostat.celsius_to_fahrenheit(30), 86.0
        )

        # Reject extreme Celsius values that overflow during conversion.
        for temperature_c in (1e308, -1e308):
            with self.subTest(temperature_c=temperature_c):
                with self.assertRaises(ValueError):
                    self.thermostat.celsius_to_fahrenheit(temperature_c)


    def test_invalid_temperature_readings(self):
        """Verify invalid temperature readings are rejected."""

        # Test missing, nonnumeric, boolean, non-finite, and oversized values.
        invalid_values = (
            None, "error", True, float("nan"), float("inf"), 10**400
        )

        for value in invalid_values:
            with self.subTest(value=repr(value)):

                # Reject invalid readings during validation.
                with self.assertRaises(ValueError):
                    self.thermostat.validate_temperature(value)

                # Prevent invalid readings from affecting LED decisions.
                with self.assertRaises(ValueError):
                    self.thermostat.get_led_states(value)

                # Prevent invalid readings from being converted.
                with self.assertRaises(ValueError):
                    self.thermostat.celsius_to_fahrenheit(value)

                # Prevent invalid readings from entering serial output.
                with self.assertRaises(ValueError):
                    self.thermostat.format_serial_status(value)

    def test_serial_status(self):
        """Verify the original serial message format is preserved."""

        # Switch to HEAT mode and generate a serial status message.
        self.thermostat.cycle_mode()
        status = self.thermostat.format_serial_status(68.5)

        # Confirm the mode, temperature, setpoint, and newline.
        self.assertEqual(status, "heat,68.5,72\n")


    def test_temperature_history_integration(self):
        """Verify the thermostat core processes temperature history."""
        
        # Submit three temperatures to verify the running average
        # is updated correctly through the thermostat controller.
        self.assertEqual(
            self.thermostat.process_temperature_reading(70), 70.0
        )
        self.assertEqual(
            self.thermostat.process_temperature_reading(72), 71.0
        )
        self.assertEqual(
            self.thermostat.process_temperature_reading(74), 72.0
        )

        self.assertEqual(
            list(self.thermostat.temperature_history.readings),
            [70.0, 72.0, 74.0]
        )
        
if __name__ == "__main__":
    # Run all tests when this file is executed directly.
    unittest.main()
