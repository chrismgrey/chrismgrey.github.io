# CS-499 Milestone Three - Algorithms and Data Structures
# Temperature History Automated Tests
#
# Verifies queue behavior, rolling averages, abnormal reading
# detection, and recovery without Raspberry Pi hardware.

import unittest

from temperature_history import TemperatureHistory


class TestTemperatureHistory(unittest.TestCase):
    """Test temperature history and abnormal reading detection."""

    def setUp(self):
        """Create an empty history before each test."""

        # Give each test a fresh queue so previous readings
        # cannot affect the results of another test.
        self.history = TemperatureHistory()

    def test_empty_history(self):
        """Verify an empty queue has no average."""

        # Confirm a new history starts without stored readings.
        self.assertEqual(len(self.history.readings), 0)

        # An empty queue should not calculate an average or
        # contain a running total from previous readings.
        self.assertIsNone(self.history.average)
        self.assertEqual(self.history.running_total, 0.0)

    def test_partial_queue_average(self):
        """Verify averaging works with fewer than five readings."""

        # Add two readings to verify the algorithm works before
        # the five-reading queue reaches its maximum capacity.
        self.history.add_reading(70)
        self.history.add_reading(72)

        # Confirm both readings are stored and the average
        # is calculated correctly using the available values.
        self.assertEqual(len(self.history.readings), 2)
        self.assertAlmostEqual(self.history.average, 71.0)
        self.assertEqual(self.history.last_status, "accepted")

    def test_five_reading_queue(self):
        """Verify the oldest reading is removed when full."""

        # Submit six readings to a queue with a maximum
        # capacity of five to test first-in, first-out behavior.
        for temperature in [71, 72, 72, 73, 72, 74]:
            self.history.add_reading(temperature)

        # Verify the oldest reading was removed and only
        # the five most recent readings remain in the queue.
        self.assertEqual(
            list(self.history.readings),
            [72.0, 72.0, 73.0, 72.0, 74.0]
        )
        self.assertEqual(len(self.history.readings), 5)

        # Confirm the running total and rolling average
        # were updated correctly after removing a reading.
        self.assertAlmostEqual(self.history.running_total, 363.0)
        self.assertAlmostEqual(self.history.average, 72.6)

    def test_normal_temperature_changes(self):
        """Verify normal fluctuations are accepted."""

        # Add several temperatures with small changes to
        # simulate normal fluctuations in room temperature.
        for temperature in [70, 72, 73, 74]:
            self.history.add_reading(temperature)

        # Verify these readings are accepted without being
        # incorrectly identified as abnormal temperature spikes.
        self.assertEqual(self.history.last_status, "accepted")
        self.assertAlmostEqual(self.history.average, 72.25)
        self.assertEqual(len(self.history.readings), 4)

    def test_abnormal_spike_flagged(self):
        """Verify a sudden spike does not enter the queue."""

        # Establish a normal temperature baseline before
        # introducing a reading that differs significantly.
        for temperature in [71, 72, 72, 73, 72]:
            self.history.add_reading(temperature)

        # Submit a sudden 90-degree reading to trigger
        # the abnormal temperature detection threshold.
        self.history.add_reading(90)

        # Confirm the unusual reading is flagged and held
        # for confirmation rather than entering the queue.
        self.assertEqual(self.history.last_status, "flagged")
        self.assertEqual(self.history.pending_reading, 90.0)

        # Verify the original temperature history and
        # rolling average remain unchanged after the spike.
        self.assertAlmostEqual(self.history.average, 72.0)
        self.assertEqual(len(self.history.readings), 5)

    def test_recovery_after_spike(self):
        """Verify normal readings clear a suspected spike."""

        # Establish a normal temperature history and
        # introduce an unusual reading of 90 degrees.
        for temperature in [71, 72, 72, 73, 72]:
            self.history.add_reading(temperature)

        self.history.add_reading(90)

        # Return to a normal temperature to simulate
        # a temporary sensor spike rather than a real change.
        self.history.add_reading(72)

        # Verify the suspected spike is cleared and
        # normal temperature processing resumes.
        self.assertEqual(self.history.last_status, "accepted")
        self.assertIsNone(self.history.pending_reading)

        # Confirm the normal reading enters the queue
        # while the oldest reading is removed.
        self.assertEqual(
            list(self.history.readings),
            [72.0, 72.0, 73.0, 72.0, 72.0]
        )

    def test_confirmed_temperature_change(self):
        """Verify consecutive unusual readings reset history."""

        # Build a normal temperature baseline before
        # introducing a sustained temperature change.
        for temperature in [71, 72, 72, 73, 72]:
            self.history.add_reading(temperature)

        # Submit two similar unusual readings to confirm
        # that the temperature may have genuinely changed.
        self.history.add_reading(90)
        self.history.add_reading(91)

        # Verify the algorithm identifies a confirmed change
        # instead of treating both readings as separate spikes.
        self.assertEqual(
            self.history.last_status, "confirmed_change"
        )

        # Confirm the previous history is cleared and
        # a new baseline begins with the confirmed reading.
        self.assertEqual(list(self.history.readings), [91.0])
        self.assertAlmostEqual(self.history.average, 91.0)

        # The pending reading should be cleared after
        # the new temperature baseline is established.
        self.assertIsNone(self.history.pending_reading)

    def test_invalid_temperature_readings(self):
        """Verify invalid and out-of-range values are rejected."""

        # Establish a valid starting temperature so we can
        # verify rejected inputs do not modify existing history.
        self.history.add_reading(72)

        # Include missing values, text, booleans, non-finite
        # numbers, and temperatures outside the allowed range.
        invalid_values = [
            None,
            "error",
            True,
            float("nan"),
            float("inf"),
            float("-inf"),
            31.9,
            120.1,
            10**1000,
            -(10**1000)

        ]

        # Test each invalid input independently to ensure
        # the algorithm rejects it with a ValueError.
        for value in invalid_values:
            with self.subTest(value=repr(value)):
                with self.assertRaises(ValueError):
                    self.history.add_reading(value)

                # Rejected input must not corrupt the history.
                self.assertEqual(
                    list(self.history.readings), [72.0]
                )
                self.assertAlmostEqual(self.history.average, 72.0)


if __name__ == "__main__":
    # Run the temperature-history tests when executed directly.
    unittest.main()
