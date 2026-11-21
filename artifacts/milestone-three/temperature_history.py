# CS-499 Milestone Three - Algorithms and Data Structures
# Temperature History
#
# Maintains a bounded queue of recent temperature readings,
# calculates a rolling average, and detects unusual changes.

from collections import deque
from math import isfinite


class TemperatureHistory:
    """Manage recent temperature readings and detect abnormal changes."""

    # Maximum number of accepted readings.
    WINDOW_SIZE = 5

    # Initial thresholds for unusual temperature changes.
    SPIKE_THRESHOLD = 8.0
    CONFIRMATION_TOLERANCE = 3.0

    # Require a small baseline before checking for spikes.
    MIN_BASELINE_READINGS = 3

    # Expected indoor temperature range in Fahrenheit.
    MIN_TEMPERATURE = 32.0
    MAX_TEMPERATURE = 120.0

    def __init__(self):
        # Create the bounded temperature history.
        self.readings = deque()
        self.running_total = 0.0

        # Track a suspected unusual reading.
        self.pending_reading = None
        self.last_status = "empty"

    def add_reading(self, temperature_f):
        """Process a reading and return the current rolling average."""
        
        # Validate the input type before processing the reading.
        if (
            isinstance(temperature_f, bool)
            or not isinstance(temperature_f, (int, float))
        ):
            raise ValueError("Invalid temperature reading.")

        # Reject temperatures outside the expected range before
        # converting the input to a float.
        if (
            temperature_f < self.MIN_TEMPERATURE
            or temperature_f > self.MAX_TEMPERATURE
        ):
            raise ValueError("Temperature outside expected range.")

        # Reject non-finite values before storing the reading.
        if not isfinite(temperature_f):
            raise ValueError("Invalid temperature reading.")

        temperature_f = float(temperature_f)

        # Check unusual changes after collecting a baseline.
        if len(self.readings) >= self.MIN_BASELINE_READINGS:
            difference = abs(temperature_f - self.average)

            if difference > self.SPIKE_THRESHOLD:

                # Confirm a suspected change using the next reading.
                if (
                    self.pending_reading is not None
                    and abs(temperature_f - self.pending_reading)
                    <= self.CONFIRMATION_TOLERANCE
                ):
                    # Begin a fresh history for the confirmed change.
                    self.readings.clear()
                    self.running_total = 0.0
                    self.pending_reading = None

                    self._store_reading(temperature_f)
                    self.last_status = "confirmed_change"
                    return self.average

                # Flag the unusual reading without adding it.
                self.pending_reading = temperature_f
                self.last_status = "flagged"
                return self.average

        # Accept a normal reading and clear any pending spike.
        self.pending_reading = None
        self._store_reading(temperature_f)
        self.last_status = "accepted"

        return self.average

    def _store_reading(self, temperature_f):
        """Update the FIFO queue and running total."""

        # Remove the oldest reading when the queue is full.
        if len(self.readings) == self.WINDOW_SIZE:
            oldest = self.readings.popleft()
            self.running_total -= oldest

        # Store the new reading and update the total.
        self.readings.append(temperature_f)
        self.running_total += temperature_f

    @property
    def average(self):
        """Return the rolling average or None if history is empty."""

        if not self.readings:
            return None

        return self.running_total / len(self.readings)
