# CS-499 Computer Science Capstone
## Raspberry Pi Thermostat - Software Design and Engineering Enhancement

### Project Overview

This project is an enhanced version of a Raspberry Pi thermostat that I originally developed in CS-350 Emerging Systems Architectures and Technologies at Southern New Hampshire University.

The original thermostat uses a Raspberry Pi 4, an AHT20 temperature sensor, a 16x2 LCD display, three buttons, and two LEDs. It supports OFF, HEAT, and COOL operating modes, allows the user to adjust the temperature setpoint, and sends thermostat information over a serial connection.

For the CS-499 capstone, I selected this project because it gave me an opportunity to revisit working code and improve how it was organized. My main focus for Milestone Two was separating the thermostat's control logic from its hardware-specific operations, making the application easier to maintain, test, and enhance.

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

### Project Files

[**original.py**](../original/original.py)

The original thermostat code from CS-350. This file has been preserved without modifications so it can be compared with the enhanced version.

**enhanced.py**

The enhanced Raspberry Pi thermostat application. It manages the temperature sensor, LCD display, physical buttons, LED indicators, and serial communication. It uses the independent ThermostatCore module for operating modes, setpoint adjustments, and temperature decisions.

**thermostat_core.py**

Contains the hardware-independent ThermostatCore class. This module manages operating modes, setpoint limits, temperature conversion, input validation, LED decisions, and serial status formatting.

**simulation.py**

An interactive desktop simulation of the enhanced thermostat. It allows the user to change operating modes, adjust the setpoint, enter simulated room temperatures, and view LED behavior without connecting to a Raspberry Pi.

**test_thermostat.py**

Contains automated unit tests for the ThermostatCore module. The tests verify operating modes, setpoint adjustments, temperature conversion, invalid temperature handling, LED behavior, and serial output.

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

The automated tests use Python's built-in unittest framework.

From the project folder, run:

    py -m unittest test_thermostat -v

The test suite contains eight test methods covering the thermostat's main control functions, including temperature validation and boundary conditions.

These tests can run on a Windows computer without Raspberry Pi hardware.

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

The application sends a comma-delimited status message containing the operating mode, current Fahrenheit temperature, and temperature setpoint approximately every 30 seconds.

Example:

    heat,68.5,72

The hardware-specific application has not been physically retested as part of this enhancement. Validation for Milestone Two was performed using the desktop simulation, automated unit tests, and simulated hardware integration tests.

### Future Enhancements

This software engineering enhancement provides the foundation for the remaining CS-499 capstone work.

Planned improvements include using algorithms and data structures to process multiple temperature readings and adding database functionality to store historical thermostat information.

These additional features are not included in the current Milestone Two implementation.

### Project Status

The Milestone Two software design and engineering enhancement is complete. The enhanced code has been reviewed, and the automated tests and desktop simulation have been verified.

The original CS-350 artifact remains unchanged for comparison with the enhanced implementation.
