# CS-499 Milestone Two - Software Design and Engineering
# Thermostat Core
#
# Handles thermostat operating modes and temperature settings
# independently of Raspberry Pi hardware.


from math import isfinite
# Import temperature history to support rolling averages and spike detection.
from temperature_history import TemperatureHistory


class ThermostatCore:
    """Manage thermostat operating modes and setpoint."""

    # Define the available operating modes in cycle order.
    MODES = ("off", "heat", "cool")

    # Define safe operating limits for the thermostat setpoint.
    MIN_SETPOINT = 50
    MAX_SETPOINT = 90

    def __init__(self):
        # Initialize the thermostat in OFF mode at 72 degrees.
        self.mode = "off"
        self.setpoint = 72
        # Maintain a shared history of accepted temperatures.
        self.temperature_history = TemperatureHistory()

    def cycle_mode(self):
        """Advance to the next thermostat operating mode."""

        # Find the current mode and advance to the next one.
        current_index = self.MODES.index(self.mode)
        next_index = (current_index + 1) % len(self.MODES)

        # Update and return the active operating mode.
        self.mode = self.MODES[next_index]
        return self.mode
    
    def increase_setpoint(self):
        """Increase the setpoint without exceeding the maximum limit."""

        # Raise the target temperature by one degree if below the maximum.
        if self.setpoint < self.MAX_SETPOINT:
            self.setpoint += 1

        return self.setpoint

    def decrease_setpoint(self):
        """Decrease the setpoint without going below the minimum limit."""

        # Lower the target temperature by one degree if above the minimum.
        if self.setpoint > self.MIN_SETPOINT:
            self.setpoint -= 1

        return self.setpoint

    def process_temperature_reading(self, temperature_f):
        """Process a new temperature and return its rolling average."""

        # Send the new reading through the queue and spike detection
        # logic before returning the calculated rolling average.
        return self.temperature_history.add_reading(temperature_f)

    def get_led_states(self, temperature_f):
        """Determine LED behavior based on mode and temperature."""
        
        # Validate the temperature before making control decisions.
        temperature_f = self.validate_temperature(temperature_f)

        # Both LEDs remain off when the thermostat is disabled.
        if self.mode == "off":
            return {"red": "off", "blue": "off"}

        # Heating mode uses the red LED.
        if self.mode == "heat":
            if temperature_f < self.setpoint:
                return {"red": "pulse", "blue": "off"}
            return {"red": "on", "blue": "off"}

        # Cooling mode uses the blue LED.
        if self.mode == "cool":
            if temperature_f > self.setpoint:
                return {"red": "off", "blue": "pulse"}
            return {"red": "off", "blue": "on"}

        # Default to both LEDs off if the mode is unrecognized.
        return {"red": "off", "blue": "off"}

    @staticmethod
    def celsius_to_fahrenheit(temperature_c):
        """Convert a Celsius temperature reading to Fahrenheit."""

        # Validate the Celsius reading before converting it.
        temperature_c = ThermostatCore.validate_temperature(temperature_c)

        # Convert the sensor temperature using the standard formula.
        temperature_f = (temperature_c * 9 / 5) + 32

        # Validate the converted result before returning it.
        return ThermostatCore.validate_temperature(temperature_f)

    def format_serial_status(self, temperature_f):
        """Format thermostat information for serial communication."""

        # Validate the temperature before formatting serial data.
        temperature_f = self.validate_temperature(temperature_f)

        # Preserve the original comma-delimited format for compatibility.
        # Include the operating mode, Fahrenheit temperature, and setpoint.
        status = f"{self.mode},{temperature_f:.1f},{self.setpoint}\n"

        return status

    @staticmethod
    def validate_temperature(temperature):
        """Validate a temperature reading before processing."""

        # Reject missing values, text, booleans, and invalid numbers.
        try:
            valid = (
                not isinstance(temperature, bool)
                and isinstance(temperature, (int, float))
                and isfinite(temperature)
            )
        except OverflowError:
            valid = False

        if not valid:
            raise ValueError("Invalid temperature reading.")

        # Return the validated temperature for further processing.
        return temperature
