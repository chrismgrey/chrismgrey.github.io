# CS-499 Computer Science Capstone

## Raspberry Pi Thermostat - Software Engineering, Algorithms, and Database Enhancements

### Project Overview

This project is an enhanced version of a Raspberry Pi thermostat that I originally developed in CS-350 Emerging Systems Architectures and Technologies at Southern New Hampshire University.

The original thermostat uses a Raspberry Pi 4, an AHT20 temperature sensor, a 16x2 LCD display, three buttons, and two LEDs. It supports OFF, HEAT, and COOL operating modes, allows the user to adjust the temperature setpoint, and sends thermostat information over a serial connection.

For the CS-499 capstone, I selected this project because it gave me an opportunity to revisit working code and improve how it was organized. My main focus for Milestone Two was separating the thermostat's control logic from its hardware-specific operations, making the application easier to maintain, test, and enhance.

For Milestone Three, I built on those improvements by adding a five-reading temperature history, a rolling average, and logic to detect unusual temperature readings. The algorithm also checks consecutive unusual readings to help distinguish temporary sensor spikes from actual temperature changes. I integrated these improvements into the desktop simulation and Raspberry Pi application and added automated tests to verify the new functionality.

For Milestone Four, I added an SQLite database to store historical temperature readings and changes to the thermostat's operating settings. This allows the application to preserve information between sessions and retrieve previous readings for analysis. I also added SQL queries to calculate minimum, maximum, and average temperatures over selected periods, along with input validation, parameterized queries, and error handling to help protect the stored data. The database functionality is integrated into both the desktop simulation and Raspberry Pi application.


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

### Database Enhancements

For Milestone Four, I added SQLite database functionality to the thermostat using Python's built-in sqlite3 library. The database stores temperature readings, timestamps, operating modes, and setpoints so that historical information remains available after the application closes.

The database uses two tables. The temperature_readings table stores accepted temperature measurements along with the thermostat's operating mode and setpoint at the time of the reading. The thermostat_events table records changes to operating modes and temperature setpoints, including the previous and new values.

I also added methods to retrieve historical temperature readings and filter them by date. SQL queries calculate the number of readings along with the minimum, maximum, and average temperatures for a selected period. This provides a way to review previous temperature measurements rather than relying only on the five readings maintained in memory.

To improve data integrity, I added input validation, SQLite constraints, and parameterized SQL queries. Database errors are handled separately so they do not unnecessarily interrupt thermostat operations. The application also avoids recording duplicate cached readings and excludes unusual temperature readings until a change is confirmed.

The database is integrated into both the desktop simulation and the Raspberry Pi application code. I added automated tests to verify database initialization, persistent storage, historical queries, input validation, and the connection between database recording and the thermostat's existing functionality.


### Project Files

[**original.py**](../original/original.py)

The original thermostat code from CS-350. This file has been preserved without modifications so it can be compared with the enhanced version.

**enhanced.py**

The enhanced Raspberry Pi thermostat application. It manages the temperature sensor, LCD display, physical buttons, LED indicators, and serial communication. It uses the independent ThermostatCore module for operating modes, setpoint adjustments, and temperature decisions. It also records accepted sensor readings and changes to operating modes and setpoints in a local SQLite database.

**thermostat_core.py**

Contains the hardware-independent ThermostatCore class. This module manages operating modes, setpoint limits, temperature conversion, input validation, LED decisions, and serial status formatting.

**temperature_history.py**

Contains the TemperatureHistory class added for Milestone Three. This module manages the five-reading queue, calculates the rolling average using a running total, and identifies unusual temperature readings. It also includes confirmation logic to distinguish temporary sensor spikes from sustained temperature changes.

**thermostat_database.py**

Contains the ThermostatDatabase class added for Milestone Four. This module uses SQLite to store temperature readings, operating modes, setpoints, and settings changes. It also provides methods for retrieving historical readings, filtering records by date, and calculating minimum, maximum, and average temperatures. Input validation, parameterized SQL queries, and database constraints help protect the stored information.

**simulation.py**

An interactive desktop simulation of the enhanced thermostat. It allows the user to change operating modes, adjust the setpoint, enter simulated room temperatures, and view LED behavior without connecting to a Raspberry Pi. It also records accepted temperature readings and changes to operating modes and setpoints in the SQLite database, allowing the stored information to be retrieved between simulation sessions.

**test_thermostat.py**

Contains automated unit tests for the ThermostatCore module. The tests verify operating modes, setpoint adjustments, temperature conversion, invalid temperature handling, LED behavior, and serial output.

**test_temperature_history.py**

Contains eight automated tests for the TemperatureHistory class. These tests verify the five-reading queue, rolling average calculations, normal temperature fluctuations, abnormal-reading detection, and recovery after unusual readings. They also check that invalid temperatures are rejected without affecting the stored history.

**test_hardware_integration.py**

Contains seven automated tests for temperature processing in the Raspberry Pi application. These tests use simulated sensor readings and a controlled timer to verify temperature caching, cache expiration, invalid sensor readings, recovery after errors, abnormal temperature spikes, confirmed temperature changes, and sensor communication failures. The tests validate the actual getFahrenheit() method without requiring physical Raspberry Pi hardware.

**test_thermostat_database.py**

Contains 14 automated tests for the ThermostatDatabase class. These tests verify database initialization, persistent storage, temperature statistics, historical queries, date filtering, input validation, and database constraints. The tests also check fractional-second timestamp filtering and confirm that unchanged thermostat settings do not create unnecessary records.

**test_hardware_database_integration.py**

Contains nine automated tests that verify SQLite recording in the Raspberry Pi thermostat application using simulated hardware. These tests check that accepted sensor readings and physical button changes are saved correctly, cached readings are not duplicated, and unusual temperatures are excluded until confirmed. They also verify setpoint limits, database error handling, and that database writes occur outside the sensor lock. The tests include checking that setting changes are still recorded when an LED update fails.

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

The simulation also uses a local SQLite database named thermostat.db, which is created in the project folder if it does not already exist. It automatically saves the initial temperature reading, accepted temperature changes, and adjustments to the operating mode or setpoint.

The database retains its records after the simulation closes, allowing temperature history and thermostat setting changes to be reviewed later. SQLite is included with Python, so no additional database software is required.

To view the stored temperature statistics, open a terminal in the project folder and run:

    py -c "from thermostat_database import ThermostatDatabase; print(ThermostatDatabase().get_temperature_statistics())"

This displays the total number of recorded temperatures along with the minimum, maximum, and average values. The query does not modify the stored records.

### Running the Automated Tests

The automated tests use Python's built-in unittest framework and can run on a Windows computer without Raspberry Pi hardware.

Open a terminal in the project folder and run:

    py -m unittest test_thermostat test_temperature_history test_hardware_integration test_thermostat_database test_hardware_database_integration -v

The complete test suite contains 47 tests across five files:

- test_thermostat.py: 9 tests covering thermostat operating modes, setpoint adjustments, temperature conversion, input validation, LED behavior, and serial output.
- test_temperature_history.py: 8 tests covering the five-reading queue, rolling average, abnormal temperature detection, and recovery.
- test_hardware_integration.py: 7 tests covering simulated sensor readings, temperature caching, cache expiration, invalid readings, abnormal temperature changes, and sensor communication failures.
- test_thermostat_database.py: 14 tests covering SQLite initialization, persistent storage, temperature statistics, date filtering, timestamp precision, input validation, and database constraints.
- test_hardware_database_integration.py: 9 tests covering accepted sensor readings, temperature caching, physical button changes, abnormal-reading detection, database failures, and database writes outside the sensor lock. The tests also verify that setting changes are recorded when an LED update fails.

All 47 automated tests passed during Milestone Four development.

The database tests use temporary SQLite files to avoid modifying the application's stored records. The hardware integration tests use simulated sensors and controlled timing to test the Raspberry Pi application's methods without requiring physical hardware.

These tests verify the thermostat's core logic, temperature-history processing, database functionality, and simulated hardware interactions. The enhanced application has not been physically retested on the Raspberry Pi as part of Milestone Four.

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

The Raspberry Pi application also records accepted sensor readings and changes made through the physical buttons in a local SQLite database named thermostat.db. The database is stored in the same directory as enhanced.py. Cached sensor readings and unconfirmed temperature spikes do not create additional records. Database errors are handled separately so the thermostat can continue operating if SQLite is unavailable.

The Milestone Four changes have not been physically retested on Raspberry Pi hardware. Validation was performed using the desktop simulation, automated database tests, and simulated hardware integration tests.

### Future Enhancements

With the software engineering, algorithms and data structures, and database enhancements completed, there are still opportunities to expand the thermostat's functionality.

One possible improvement would be adding daily and weekly temperature reports using the historical information stored in SQLite. A simple dashboard could also make it easier to review temperature trends and thermostat activity without running database queries manually.

Another improvement would be adding a database retention policy to manage older records and limit storage usage during long-term operation. I would also like to test the completed enhancements on the physical Raspberry Pi hardware to confirm that the database integration performs as expected with the sensor, buttons, and display.

### Project Status

The Milestone Two software design and engineering enhancement, Milestone Three algorithms and data structures enhancement, and Milestone Four database enhancement are complete.

The thermostat now includes independent control logic, a five-reading temperature history, rolling average calculations, abnormal temperature detection, temperature caching, and SQLite database storage. Temperature readings and thermostat setting changes are now stored between sessions. Historical temperature readings can also be retrieved and analyzed using the database queries.

The desktop simulation has been tested successfully with database recording, and all 47 automated tests passed during Milestone Four development. These tests cover the thermostat's core functionality, temperature-history processing, database operations, and simulated hardware integration, including recording setting changes when an LED update fails.

The original CS-350 artifact remains unchanged for comparison. The enhanced Raspberry Pi application has been tested using simulated hardware dependencies, but the Milestone Four changes have not been physically retested on the Raspberry Pi.
