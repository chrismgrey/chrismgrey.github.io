# CS-499 Milestone Two - Software Design and Engineering
# Desktop Thermostat Simulation
#
# Simulates the enhanced thermostat using standard Python.
# Allows testing of operating modes, temperature adjustments,
# and LED decisions without requiring Raspberry Pi hardware.


from thermostat_core import ThermostatCore


def display_status(thermostat, temperature_f):
    """Display the current thermostat settings and LED states."""

    # Obtain heating and cooling decisions from the thermostat core.
    led_states = thermostat.get_led_states(temperature_f)

    # Display the current operating conditions.
    print("\n" + "=" * 45)
    print("THERMOSTAT STATUS")
    print("=" * 45)
    print(f"Operating Mode:    {thermostat.mode.upper()}")
    print(f"Room Temperature:  {temperature_f:.1f} F")
    print(f"Temperature Set:   {thermostat.setpoint} F")

    # Display simulated LED behavior.
    print(f"Red LED (Heat):    {led_states['red'].upper()}")
    print(f"Blue LED (Cool):   {led_states['blue'].upper()}")

    # Display the serial message without printing its newline.
    serial_status = thermostat.format_serial_status(temperature_f)
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


def change_temperature(thermostat, current_temperature):
    """Accept and validate a simulated room temperature."""

    try:
        # Request a Fahrenheit temperature from the user.
        user_input = input("Enter room temperature (F): ")
        temperature_f = float(user_input)

        # Validate the reading before using it in the simulation.
        thermostat.validate_temperature(temperature_f)

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

    # Start with a simulated room temperature of 72 degrees.
    temperature_f = 72.0

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
                # Advance through OFF, HEAT, and COOL.
                new_mode = thermostat.cycle_mode()
                print(f"Operating mode changed to {new_mode.upper()}")

            elif choice == "2":
                # Increase the setpoint within the configured limit.
                new_setpoint = thermostat.increase_setpoint()
                print(f"Temperature setpoint: {new_setpoint} F")

            elif choice == "3":
                # Decrease the setpoint within the configured limit.
                new_setpoint = thermostat.decrease_setpoint()
                print(f"Temperature setpoint: {new_setpoint} F")

            elif choice == "4":
                # Update the simulated temperature using validated input.
                temperature_f = change_temperature(
                    thermostat, temperature_f
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
