# CS-499 Computer Science Capstone
## Raspberry Pi Thermostat - Software Engineering and Algorithms Enhancements

### Project Overview

This project is an enhanced version of a Raspberry Pi thermostat that I originally developed in CS-350 Emerging Systems Architectures and Technologies at Southern New Hampshire University.

The original thermostat uses a Raspberry Pi 4, an AHT20 temperature sensor, a 16x2 LCD display, three buttons, and two LEDs. It supports OFF, HEAT, and COOL operating modes, allows the user to adjust the temperature setpoint, and sends thermostat information over a serial connection.

For the CS-499 capstone, I selected this project because it gave me an opportunity to revisit working code and improve how it was organized. My main focus for Milestone Two was separating the thermostat's control logic from its hardware-specific operations, making the application easier to maintain, test, and enhance.

For Milestone Three, I built on those improvements by adding a five-reading temperature history, a rolling average, and logic to detect unusual temperature readings. The algorithm also checks consecutive unusual readings to help distinguish temporary sensor spikes from actual temperature changes. I integrated these improvements into the desktop simulation and Raspberry Pi application and added automated tests to verify the new functionality.

### Software Engineering Enhancements

The original thermostat combined its operating logic and Raspberry Pi hardware interactions in one Python file. While the application worked, this made it difficult to test without having the physical hardware connected.

The enhanced version includes several improvements:

- Separated thermostat control logic into an independent Python module.
- Preserved the original OFF, HEAT, and COOL operating modes.
- Added temperature setpoint limits between 50°F and 90°F.
- Added validation to reject invalid temperature readings.
- Improved error handling and hardware resource cleanup.
- Created a desktop simulation that does not require Raspberry Pi hardware.
- Added automated unit tests to verify the thermostat's core functionality.

These changes allow the thermostat's main control logic to be tested independently while keeping the existing hardware functionality in the Raspberry Pi application.

### Algorithms and Data Structures Enhancements

For Milestone Three, I added a TemperatureHistory class to improve how the thermostat handles incoming temperature readings. Instead of relying on individual readings, the thermostat now maintains a queue containing the five most recent accepted temperatures.

The queue uses Python's deque collection and a running total to calculate a rolling average. When the queue reaches five readings, the oldest value is removed before a new one is added. This keeps the amount of stored data consistent and allows the average to be updated efficiently without recalculating the entire history each time.

I also added logic to identify unusual temperature readings before they are included in the rolling average. Once at least three readings have established a baseline, the algorithm flags any new reading that differs from the average by more than 8°F. Instead of immediately accepting that reading, it temporarily holds it for comparison with the next sensor reading.

If the next reading is within 3°F of the flagged value, the algorithm treats the change as confirmed and starts a new temperature history. If the temperature returns to its normal range, the suspected spike is discarded and regular processing continues. This helps prevent a single unusual reading from affecting the thermostat while still allowing it to recognize sustained temperature changes.

To support these improvements in the Raspberry Pi application, I also added temperature caching and a one-second sampling interval. The application uses a monotonic timer to determine when a new sensor reading is needed. If another part of the thermostat requests a temperature within that interval, the previously processed value is reused instead of collecting another reading. The existing sensor lock also protects the temperature processing and caching operations from overlapping requests. This allows the LCD, LED indicators, and serial communication to share the processed temperature without adding unnecessary readings to the queue.

### Project Files

[**original.py**](../original/original.py)

The original thermostat code from CS-350. This file has been preserved without modifications so it can be compared with the enhanced version.

**enhanced.py**

The enhanced Raspberry Pi thermostat application. It manages the temperature sensor, LCD display, physical buttons, LED indicators, and serial communication. It uses the independent ThermostatCore module for operating modes, setpoint adjustments, and temperature decisions.

**thermostat_core.py**

Contains the hardware-independent ThermostatCore class. This module manages operating modes, setpoint limits, temperature conversion, input validation, LED decisions, and serial status formatting.

**temperature_history.py**

Contains the TemperatureHistory class added for Milestone Three. This module manages the five-reading queue, calculates the rolling average using a running total, and identifies unusual temperature readings. It also includes confirmation logic to distinguish temporary sensor spikes from sustained temperature changes.

**simulation.py**

An interactive desktop simulation of the enhanced thermostat. It allows the user to change operating modes, adjust the setpoint, enter simulated room temperatures, and view LED behavior without connecting to a Raspberry Pi.

**test_thermostat.py**

Contains automated unit tests for the ThermostatCore module. The tests verify operating modes, setpoint adjustments, temperature conversion, invalid temperature handling, LED behavior, and serial output.

**test_temperature_history.py**

Contains eight automated tests for the TemperatureHistory class. These tests verify the five-reading queue, rolling average calculations, normal temperature fluctuations, abnormal-reading detection, and recovery after unusual readings. They also check that invalid temperatures are rejected without affecting the stored history.

**test_hardware_integration.py**

Contains seven automated tests for temperature processing in the Raspberry Pi application. These tests use simulated sensor readings and a controlled timer to verify temperature caching, cache expiration, invalid sensor readings, recovery after errors, abnormal temperature spikes, confirmed temperature changes, and sensor communication failures. The tests validate the actual getFahrenheit() method without requiring physical Raspberry Pi hardware.

### Running the Desktop Simulation

The desktop simulation requires Python 3 and does not need any Raspberry Pi hardware or additional third-party packages.

Open a terminal in the project folder and run:

    py simulation.py

The simulation provides a menu with the following options:

1. Cycle through OFF, HEAT, and COOL modes.
2. Increase the temperature setpoint.
3. Decrease the temperature setpoint.
4. Enter a simulated room temperature.
5. Refresh the thermostat status.
6. Exit the simulation.

The displayed status includes the current operating mode, room temperature, setpoint, simulated LED behavior, and serial output.

### Running the Automated Tests

The automated tests use Python's built-in unittest framework and can run on a Windows computer without Raspberry Pi hardware.

Open a terminal in the project folder and run:

    py -m unittest test_thermostat test_temperature_history test_hardware_integration -v

The complete test suite contains 24 tests across three files:

- test_thermostat.py: 9 tests covering thermostat operating modes, setpoint adjustments, temperature conversion, input validation, LED behavior, and serial output.
- test_temperature_history.py: 8 tests covering the five-reading queue, rolling average, abnormal temperature detection, and recovery.
- test_hardware_integration.py: 7 tests covering simulated sensor readings, temperature caching, cache expiration, invalid readings, abnormal temperature changes, and sensor communication failures.

All 24 automated tests passed during Milestone Three development.

These tests verify the thermostat's core logic and simulated hardware interactions. Physical Raspberry Pi hardware testing has not been repeated as part of this enhancement.

### Running on Raspberry Pi

The enhanced hardware application is intended for the original Raspberry Pi 4 thermostat configuration.

It requires the appropriate Raspberry Pi hardware libraries, including support for GPIO, the AHT20 sensor, the character LCD, and serial communication. The application imports board, digitalio, adafruit_ahtx0, adafruit_character_lcd, gpiozero, and serial.

The hardware configuration uses:

- AHT20 temperature sensor connected through I2C.
- 16x2 LCD connected using GPIO 17, 27, 5, 6, 13, and 26.
- Red LED connected to GPIO 18.
- Blue LED connected to GPIO 23.
- Mode selection button connected to GPIO 24.
- Setpoint increase button connected to GPIO 25.
- Setpoint decrease button connected to GPIO 12.
- UART communication configured for /dev/ttyS0 at 115200 baud.

I2C and serial communication must be configured appropriately on the Raspberry Pi.

With the required hardware and libraries installed, the application can be started using:

    python3 enhanced.py

The enhanced application uses the processed temperature from the rolling average for its LCD display, heating and cooling LED decisions, and serial communication. Temperature caching prevents repeated requests within one second from adding unnecessary sensor readings to the history.

The application sends a comma-delimited status message containing the operating mode, processed Fahrenheit temperature, and temperature setpoint approximately every 30 seconds.

Example:

    heat,68.5,72

The hardware-specific application has not been physically retested as part of Milestone Three. Validation for this enhancement was performed using the desktop simulation, automated unit tests, and simulated hardware integration tests.

### Future Enhancements

The software engineering and algorithms and data structures enhancements provide the foundation for the final CS-499 capstone improvement.

The remaining enhancement will focus on database functionality using SQLite to store historical thermostat information. This will allow temperature readings and thermostat activity to be saved and retrieved rather than existing only while the application is running.

The database enhancement is planned for Milestone Four and is not included in the current implementation.

### Project Status

The Milestone Two software design and engineering enhancement and Milestone Three algorithms and data structures enhancement are complete.

The thermostat now includes independent control logic, a five-reading temperature history, rolling average calculations, abnormal temperature detection, and temperature caching. The desktop simulation has been verified, and all 24 automated tests passed successfully.

The original CS-350 artifact remains unchanged for comparison. The enhanced Raspberry Pi application has been checked through automated testing and simulated hardware interactions, but it has not been physically retested on the Raspberry Pi.

The remaining capstone enhancement will add SQLite database functionality for storing historical thermostat information.
