# CS-499 Computer Science Capstone
# Desktop Thermostat Simulation
#
# Simulates the enhanced thermostat using standard Python.
# Allows testing of operating modes, temperature adjustments,
# rolling averages, and LED decisions without Raspberry Pi hardware.
# Records accepted temperature readings and setting changes in SQLite.


import sqlite3
from pathlib import Path

from thermostat_core import ThermostatCore
from thermostat_database import ThermostatDatabase

def record_temperature(database, thermostat, temperature_f):
    """Save accepted readings without interrupting the simulation."""

    # Do not save an unusual reading that was flagged by the history logic.
    if database is None or thermostat.temperature_history.last_status == "flagged":
        return

    try:
        database.save_temperature_reading(
            temperature_f, thermostat.mode, thermostat.setpoint
        )
    except (sqlite3.Error, OSError, ValueError) as error:
        # Keep the simulation usable if saving to SQLite fails.
        print(f"Database warning: Reading was not saved ({error}).")

def record_setting(database, event_type, previous_value, new_value):
    """Save settings changes without interrupting the simulation."""

    if database is None:
        return

    try:
        database.save_setting_change(event_type, previous_value, new_value)
    except (sqlite3.Error, OSError, ValueError) as error:
        # A database failure should not prevent thermostat adjustments.
        print(f"Database warning: Setting change was not saved ({error}).")

def display_status(thermostat, temperature_f):
    """Display the current thermostat settings and LED states."""

    # Use the rolling average for heating and cooling decisions
    # so a flagged temperature spike does not affect LED behavior.
    average_temperature = thermostat.temperature_history.average
    led_states = thermostat.get_led_states(average_temperature)

    # Display the current operating conditions.
    print("\n" + "=" * 45)
    print("THERMOSTAT STATUS")
    print("=" * 45)
    print(f"Operating Mode:    {thermostat.mode.upper()}")
    print(f"Room Temperature:  {temperature_f:.1f} F")
    # Show the rolling average separately so we can compare
    # the latest sensor reading with the processed temperature.
    print(f"Rolling Average:   {average_temperature:.1f} F")
    print(f"Temperature Set:   {thermostat.setpoint} F")

    # Display simulated LED behavior.
    print(f"Red LED (Heat):    {led_states['red'].upper()}")
    print(f"Blue LED (Cool):   {led_states['blue'].upper()}")

    # Use the processed temperature in the serial output so
    # flagged spikes do not affect the reported thermostat status.
    serial_status = thermostat.format_serial_status(average_temperature)
    print(f"Serial Output:     {serial_status.strip()}")
    print("=" * 45)

def display_menu():
    """Display the available thermostat simulation controls."""

    print("\nTHERMOSTAT CONTROLS")
    print("1. Cycle operating mode")
    print("2. Increase temperature setpoint")
    print("3. Decrease temperature setpoint")
    print("4. Change simulated room temperature")
    print("5. Refresh thermostat status")
    print("6. Exit simulation")

def change_temperature(thermostat, current_temperature, database):
    """Accept and validate a simulated room temperature."""

    try:
        # Request a Fahrenheit temperature from the user.
        user_input = input("Enter room temperature (F): ")
        temperature_f = float(user_input)

        # Validate the reading before using it in the simulation.
        thermostat.validate_temperature(temperature_f)

        # Process each new reading through the rolling average
        # and spike detection logic before updating the simulation.
        thermostat.process_temperature_reading(temperature_f)

        # Save the accepted temperature reading to SQLite.
        record_temperature(database, thermostat, temperature_f)

        print(f"Room temperature updated to {temperature_f:.1f} F")
        return temperature_f

    except ValueError:
        # Reject invalid values without changing the current reading.
        print("Invalid temperature. Please enter a valid number.")
        return current_temperature

def main():
    """Run the interactive desktop thermostat simulation."""

    # Initialize the hardware-independent thermostat controller.
    thermostat = ThermostatCore()


    # Initialize the SQLite database for persistent thermostat history.
    # Keep the database in the same directory as the application.
    database_path = Path(__file__).resolve().parent / "thermostat.db"

    try:
        database = ThermostatDatabase(database_path)
    except (sqlite3.Error, OSError) as error:
        # Continue running the simulation if the database is unavailable.
        print(f"Database warning: Initialization failed ({error}).")
        database = None

    # Start with a simulated room temperature of 72 degrees.
    temperature_f = 72.0

    # Add the starting temperature to establish an initial
    # reading for the rolling average.
    thermostat.process_temperature_reading(temperature_f)

    # Save the initial accepted reading to the database.
    record_temperature(database, thermostat, temperature_f)
    print("=" * 45)
    print("CS-499 ENHANCED THERMOSTAT SIMULATION")
    print("=" * 45)
    print("Running without Raspberry Pi hardware.")
    print("Use the menu to control the simulated thermostat.")

    # Continue accepting commands until the user exits.
    while True:
        try:
            # Display current conditions and available controls.
            display_status(thermostat, temperature_f)
            display_menu()

            choice = input("\nSelect an option (1-6): ").strip()

            if choice == "1":
                # Record the previous mode before changing it.
                previous_mode = thermostat.mode
                new_mode = thermostat.cycle_mode()

                # Save the operating mode change to SQLite.
                record_setting(database, "mode", previous_mode, new_mode)
                print(f"Operating mode changed to {new_mode.upper()}")

            elif choice == "2":
                # Record the previous setpoint before increasing it.
                previous_setpoint = thermostat.setpoint
                new_setpoint = thermostat.increase_setpoint()

                # Save the setpoint change to SQLite.
                record_setting(
                    database, "setpoint", previous_setpoint, new_setpoint
                )
                print(f"Temperature setpoint: {new_setpoint} F")

            elif choice == "3":
                # Record the previous setpoint before decreasing it.
                previous_setpoint = thermostat.setpoint
                new_setpoint = thermostat.decrease_setpoint()

                # Save the setpoint change to SQLite.
                record_setting(
                    database, "setpoint", previous_setpoint, new_setpoint
                )
                print(f"Temperature setpoint: {new_setpoint} F")

            elif choice == "4":
                # Update the simulated temperature and record accepted readings.
                temperature_f = change_temperature(
                    thermostat, temperature_f, database
                )

            elif choice == "5":
                # Refresh the display without modifying any settings.
                print("Refreshing thermostat status...")

            elif choice == "6":
                # Exit the simulation without accessing hardware.
                print("\nThermostat simulation ended.")
                break

            else:
                # Prevent unrecognized menu commands from changing state.
                print("Invalid option. Please select 1 through 6.")

        except (KeyboardInterrupt, EOFError):
            # Allow the simulation to exit cleanly from the terminal.
            print("\nThermostat simulation interrupted.")
            break

if __name__ == "__main__":
    # Start the simulation only when this file is run directly.
    main()
