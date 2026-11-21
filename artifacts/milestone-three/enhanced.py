# CS-499 Computer Science Capstone
# Enhanced Raspberry Pi Thermostat
#
# Originally developed for CS-350 Emerging Systems Architectures
# and Technologies. Enhanced for the CS-499 Computer Science Capstone.
#
# Purpose:
# Manage thermostat hardware while delegating operating modes,
# temperature decisions, and data formatting to ThermostatCore.
#
# Functionality:
# - Supports OFF, HEAT, and COOL operating modes.
# - Allows temperature adjustments between 50 and 90 degrees Fahrenheit.
# - Uses an AHT20 sensor to monitor room temperature.
# - Uses a five-reading rolling average with abnormal-reading detection.
# - Controls red and blue LEDs to indicate thermostat activity.
# - Displays date, time, temperature, mode, and setpoint on a 16x2 LCD.
# - Sends thermostat status over UART approximately every 30 seconds.
#
# Software Engineering Enhancements (Milestone Two):
# - Separates hardware operations from thermostat control logic.
# - Uses a reusable, hardware-independent thermostat controller.
# - Adds temperature validation and setpoint boundaries.
# - Supports automated testing without Raspberry Pi hardware.
#
# Algorithms and Data Structures Enhancements (Milestone Three):
# - Tracks five accepted temperature readings using a bounded queue.
# - Uses a running total to calculate the rolling average efficiently.
# - Detects unusual readings and confirms sustained temperature changes.
# - Caches processed temperatures using a one-second sampling interval.
# - Integrates the rolling average with LED, LCD, and serial operations.
#
# Change History:
# Version 1.0 - Original CS-350 thermostat implementation.
# Version 2.0 - CS-499 software design and engineering enhancements.
# Version 3.0 - CS-499 algorithms and data structures enhancements.


##
## Import necessary to provide timing in the main loop
##
from time import sleep

# Use a monotonic timer to control how often new sensor readings are collected.
from time import monotonic

from datetime import datetime

# Import the hardware-independent thermostat controller.
from thermostat_core import ThermostatCore

##
## Imports necessary to provide connectivity to the
## thermostat sensor and the I2C bus
##
import board
import adafruit_ahtx0

##
## These are the packages that we need to pull in so that we can work
## with the GPIO interface on the Raspberry Pi board and work with
## the 16x2 LCD display
##
# import board - already imported for I2C connectivity
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd

## This imports the Python serial package to handle communications over the
## Raspberry Pi's serial port.
import serial

##
## Imports required to handle our Button, and our PWMLED devices
##
from gpiozero import Button, PWMLED


# Thread manages LCD updates independently of the main application loop.
# Lock prevents overlapping temperature sensor readings.
from threading import Thread, Lock


##
## DEBUG flag - boolean value to indicate whether or not to print
## status messages on the console of the program
##
DEBUG = True

# Hardware resources are assigned during application startup.
# Initialize references to support safe cleanup if startup fails.
i2c = None
thSensor = None
ser = None
redLight = None
blueLight = None
screen = None
greenButton = None
redButton = None
blueButton = None


# Prevent overlapping sensor readings from the display and button callbacks.
sensorLock = Lock()

##
## ManagedDisplay - Manage the 16x2 LCD display.
##
## Originally developed during CS-350 and enhanced for CS-499
## with improved initialization and hardware cleanup.
##

class ManagedDisplay():
    def __init__(self):

        # Configure the six digital GPIO connections for the 16x2 LCD.
        # Pin assignments must match the physical LCD wiring.

        try:
            # Initialize the six LCD GPIO connections.
            self.lcd_rs = digitalio.DigitalInOut(board.D17)
            self.lcd_en = digitalio.DigitalInOut(board.D27)
            self.lcd_d4 = digitalio.DigitalInOut(board.D5)
            self.lcd_d5 = digitalio.DigitalInOut(board.D6)
            self.lcd_d6 = digitalio.DigitalInOut(board.D13)
            self.lcd_d7 = digitalio.DigitalInOut(board.D26)

            # Configure the original 16x2 LCD dimensions.
            self.lcd_columns = 16
            self.lcd_rows = 2

            # Initialize the LCD using the configured GPIO connections.
            self.lcd = characterlcd.Character_LCD_Mono(
                self.lcd_rs, self.lcd_en,
                self.lcd_d4, self.lcd_d5, self.lcd_d6, self.lcd_d7,
                self.lcd_columns, self.lcd_rows
            )

            # Clear the LCD before displaying thermostat information.
            self.lcd.clear()

        except Exception:
            # Release any GPIO connections created before setup failed.
            pin_names = (
                "lcd_rs", "lcd_en", "lcd_d4",
                "lcd_d5", "lcd_d6", "lcd_d7"
            )

            for pin_name in pin_names:
                pin = getattr(self, pin_name, None)

                if pin is not None:
                    try:
                        pin.deinit()
                    except Exception as error:
                        if DEBUG:
                            print(f"LCD pin cleanup error ({pin_name}): {error}")

            # Report the original initialization failure to main().
            raise

    def cleanupDisplay(self):
        """Clear the display and release each LCD GPIO connection."""

        # Always release GPIO connections, even if clearing the LCD fails.
        try:
            self.lcd.clear()
        except Exception as error:
            if DEBUG:
                print(f"LCD clear error during cleanup: {error}")
        finally:
            # Attempt each GPIO release independently.
            pin_names = (
                "lcd_rs", "lcd_en", "lcd_d4",
                "lcd_d5", "lcd_d6", "lcd_d7"
            )

            for pin_name in pin_names:
                pin = getattr(self, pin_name, None)
                if pin is not None:
                    try:
                        pin.deinit()
                    except Exception as error:
                        if DEBUG:
                            print(f"LCD pin cleanup error ({pin_name}): {error}")

    def updateScreen(self, message):
        self.lcd.clear()
        self.lcd.message = message

##
## TemperatureMachine - Raspberry Pi Hardware Management
##
## Handles the physical thermostat components, including sensor
## readings, LED indicators, LCD output, and serial communication.
## ThermostatCore manages operating modes and control decisions.
##
class TemperatureMachine:
    """Manage thermostat hardware and application operations."""

    # Limit new sensor samples to once per second so multiple
    # hardware functions can share the same processed reading.
    SAMPLE_INTERVAL_SECONDS = 1.0

    def __init__(self):
        """Initialize the thermostat controller and application state."""

        # Create the controller responsible for thermostat logic,
        # operating modes, and temperature settings.
        self.core = ThermostatCore()

        # Track shutdown status independently for this instance.
        self.endDisplay = False

        # Store the latest processed temperature and sample time
        # so other hardware functions can reuse the same reading.
        self.cached_temperature_f = None
        self.last_sample_time = None

    def processTempStateButton(self):
        """Cycle the thermostat mode using the reusable controller."""

        if DEBUG:
            print("Cycling Temperature State")

        # Advance the operating mode through the independent controller.
        self.core.cycle_mode()

        # Update the physical LEDs to reflect the new operating mode.
        self.updateLights()

    def processTempIncButton(self):
        """Increase the setpoint using the reusable controller."""

        if DEBUG:
            print("Increasing Set Point")

        # Increase the setpoint using the core's built-in limits.
        self.core.increase_setpoint()

        # Refresh the LED indicators after the setpoint changes.
        self.updateLights()

    def processTempDecButton(self):
        """Decrease the setpoint using the reusable controller."""

        if DEBUG:
            print("Decreasing Set Point")

        # Decrease the setpoint using the core's built-in limits.
        self.core.decrease_setpoint()

        # Refresh the LED indicators after the setpoint changes.
        self.updateLights()

    def updateLights(self):
        """Apply thermostat control decisions to the physical LEDs."""

        # Turn off both LEDs before applying the updated state.
        redLight.off()
        blueLight.off()

        try:
            # Read the current temperature and obtain LED decisions
            # from the hardware-independent thermostat controller.
            temperature_f = self.getFahrenheit()
            led_states = self.core.get_led_states(temperature_f)

        except (ValueError, OSError, RuntimeError) as error:
            # Keep both LEDs off if the sensor reading is unavailable.
            if DEBUG:
                print(f"Unable to update LEDs: {error}")
            return

        # Print current thermostat information when debugging.
        if DEBUG:
            print(f"State: {self.core.mode}")
            print(f"SetPoint: {self.core.setpoint}")
            print(f"Temp: {temperature_f}")

        # Apply the core's heating decision to the red LED.
        if led_states["red"] == "pulse":
            redLight.pulse()
        elif led_states["red"] == "on":
            redLight.on()

        # Apply the core's cooling decision to the blue LED.
        if led_states["blue"] == "pulse":
            blueLight.pulse()
        elif led_states["blue"] == "on":
            blueLight.on()

    def run(self):
        """Start the display thread and retain it for clean shutdown."""

        # Store the display thread so it can be managed during shutdown.
        self.display_thread = Thread(
            target=self.manageMyDisplay,
            name="ThermostatDisplay"
        )

        # Start the background display management routine.
        self.display_thread.start()

    def stop(self):
        """Stop the display thread and wait for it to finish."""

        # Signal the display management loop to stop running.
        self.endDisplay = True

        # Wait only if the display thread was actually started.
        display_thread = getattr(self, "display_thread", None)

        if display_thread is not None and display_thread.ident is not None:
            display_thread.join()

        elif screen is not None:
            # Release the LCD if startup failed before the thread started.
            try:
                screen.cleanupDisplay()
            except Exception as error:
                if DEBUG:
                    print(f"LCD cleanup error: {error}")

        # Release buttons first to prevent new callbacks during shutdown.
        for button in (greenButton, redButton, blueButton):
            if button is not None:
                try:
                    button.when_pressed = None
                except Exception as error:
                    if DEBUG:
                        print(f"Button callback cleanup error: {error}")
                finally:
                    try:
                        button.close()
                    except Exception as error:
                        if DEBUG:
                            print(f"Button cleanup error: {error}")

        # Turn off and release initialized LED outputs.
        for light in (redLight, blueLight):
            if light is not None:
                try:
                    light.off()
                except Exception as error:
                    if DEBUG:
                        print(f"LED shutdown error: {error}")
                finally:
                    try:
                        light.close()
                    except Exception as error:
                        if DEBUG:
                            print(f"LED cleanup error: {error}")

        # Close the UART connection if it was opened.
        if ser is not None:
            try:
                ser.close()
            except Exception as error:
                if DEBUG:
                    print(f"Serial cleanup error: {error}")

        # Release the I2C bus after sensor operations have stopped.
        if i2c is not None:
            try:
                i2c.deinit()
            except Exception as error:
                if DEBUG:
                    print(f"I2C cleanup error: {error}")

        if DEBUG:
            print("Thermostat hardware resources released.")

    def getFahrenheit(self):
        """Read the sensor and convert Celsius to Fahrenheit."""

        # Prevent overlapping sensor readings from multiple threads.
        with sensorLock:
            # Record the current time to manage the sensor sampling interval.
            current_time = monotonic()

            # Reuse the previous temperature if it was collected
            # within the sampling interval to avoid duplicate readings.
            if (
                self.cached_temperature_f is not None
                and self.last_sample_time is not None
                and current_time - self.last_sample_time < self.SAMPLE_INTERVAL_SECONDS
            ):
                return self.cached_temperature_f

            temperature_c = thSensor.temperature

            # Convert the sensor reading to Fahrenheit before
            # processing it through the rolling average and spike detection.
            temperature_f = ThermostatCore.celsius_to_fahrenheit(temperature_c)
            
            # Process the new reading through the temperature history.
            processed_temperature = self.core.process_temperature_reading(temperature_f)

            # Cache the processed temperature and sample time so other
            # hardware functions can reuse the value without another sensor read.
            self.cached_temperature_f = processed_temperature
            self.last_sample_time = monotonic()

            return processed_temperature

    def setupSerialOutput(self):
        """Prepare thermostat status for serial communication."""

        # Read the current temperature from the hardware sensor.
        temperature_f = self.getFahrenheit()

        # Let the independent controller format the status message.
        # Preserve the original format for TemperatureServer compatibility.
        return self.core.format_serial_status(temperature_f)

    def manageMyDisplay(self):
        """Manage the display and ensure LCD resources are released."""

        # Always attempt LCD cleanup when the display loop exits.
        try:
            self._manageDisplayLoop()
        finally:
            screen.cleanupDisplay()

    def _manageDisplayLoop(self):
        """Refresh LCD information and transmit thermostat status."""

        # Initialize counters for display and serial update intervals.
        counter = 1
        altCounter = 1
        while not self.endDisplay:
            # Print display-loop activity when debugging is enabled.
            if DEBUG:
                print("Processing Display Info...")

            current_time = datetime.now()

            # Show the current date and time on the first LCD line.
            lcd_line_1 = current_time.strftime("%m/%d/%y %H:%M") + "\n"

            if altCounter < 6:
                # Display the current temperature when available.
                try:
                    temperature_f = self.getFahrenheit()
                    lcd_line_2 = f"Temp: {temperature_f:.1f} F"

                except (ValueError, OSError, RuntimeError) as error:
                    # Display an error instead of stopping the display thread.
                    lcd_line_2 = "Sensor Error"

                    # Disable LED indicators when sensor data is unavailable.
                    redLight.off()
                    blueLight.off()

                    if DEBUG:
                        print(f"Temperature sensor error: {error}")

                # Continue alternating the LCD information.
                altCounter += 1

            else:
                # Show the current thermostat mode and set temperature.
                lcd_line_2 = f"{self.core.mode.upper()} Set: {self.core.setpoint} F"

                altCounter = altCounter + 1
                if altCounter >= 11:
                    # Run the routine to update the lights every 10 seconds
                    # to keep operations smooth
                    self.updateLights()
                    altCounter = 1

            ## Update Display
            screen.updateScreen(lcd_line_1 + lcd_line_2)

            ## Update server every 30 seconds
            if DEBUG:
                print(f"Counter: {counter}")
            if (counter % 30) == 0:
                # Attempt to send thermostat status over UART.
                try:
                    # Generate and transmit the validated status message.
                    status_message = self.setupSerialOutput()
                    ser.write(status_message.encode("utf-8"))

                except (ValueError, OSError, RuntimeError,
                        serial.SerialException) as error:
                    # Log sensor or serial errors without stopping the display.
                    if DEBUG:
                        print(f"Unable to send thermostat status: {error}")

                # Reset the counter for the next scheduled update.
                counter = 1
            else:
                counter += 1
            sleep(1)

def main():
    """Initialize and run the Raspberry Pi thermostat application."""

    # Make hardware resources available to the application methods.
    global greenButton, redButton, blueButton
    global i2c, thSensor, ser
    global redLight, blueLight, screen

    # Create the hardware-independent thermostat controller.
    tsm = TemperatureMachine()

    try:
        # Initialize the I2C bus and temperature sensor.
        i2c = board.I2C()
        thSensor = adafruit_ahtx0.AHTx0(i2c)

        # Initialize UART using the original communication settings.
        ser = serial.Serial(
            port="/dev/ttyS0",
            baudrate=115200,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1
        )

        # Initialize the physical LED indicators.
        redLight = PWMLED(18)
        blueLight = PWMLED(23)

        # Initialize the LCD using the original GPIO configuration.
        screen = ManagedDisplay()

        # Configure the mode button with debounce protection.
        greenButton = Button(24, bounce_time=0.1)
        greenButton.when_pressed = tsm.processTempStateButton

        # Configure the setpoint increase button.
        redButton = Button(25, bounce_time=0.1)
        redButton.when_pressed = tsm.processTempIncButton

        # Configure the setpoint decrease button.
        blueButton = Button(12, bounce_time=0.1)
        blueButton.when_pressed = tsm.processTempDecButton

        # Start display management after hardware initialization.
        tsm.run()

        # Monitor the display thread while the application is running.
        while True:
            # Detect unexpected display-thread termination.
            if not tsm.display_thread.is_alive():
                raise RuntimeError("Display thread stopped unexpectedly.")

            # Check the thread status once per second.
            sleep(1)

    except KeyboardInterrupt:
        # Handle a normal Ctrl+C shutdown.
        print("Cleaning up. Exiting...")

    except Exception as error:
        # Report unexpected startup or application errors.
        print(f"Thermostat application error: {error}")
        raise

    finally:
        # Release initialized resources regardless of how execution ends.
        tsm.stop()

if __name__ == "__main__":
    # Start the thermostat only when executed directly.
    main()