# Milestone Three: Algorithms and Data Structures

## Artifact Description

For this enhancement, I continued working with the Raspberry Pi thermostat I originally developed during CS-350 in October 2026. The application uses Python and a Raspberry Pi 4 to monitor temperature, manage heating and cooling modes, control LEDs, and display information on an LCD. In Milestone Two, I separated the control logic from the hardware operations. This enhancement focuses on improving how the thermostat processes temperature readings.

## Reason for Selecting the Artifact

I continued using this project for my ePortfolio because it was one of my more involved programming assignments and gave me an opportunity to improve different parts of the same application. One limitation I noticed during my code review was that the thermostat relied on individual sensor readings when making decisions, without considering previous temperatures.

My main improvement was creating a TemperatureHistory class that stores up to five accepted readings in a queue. I used Python's deque collection and a running total to calculate a rolling average efficiently. I also added logic to identify unusual readings and determine whether they were temporary spikes or actual temperature changes. Temperature caching was another improvement that helped prevent unnecessary sensor readings. I also added validation to reject invalid temperature readings before they could affect the stored history.

These changes demonstrate my ability to apply algorithms and data structures to improve how an existing application handles information.

## Course Outcomes

In my Module One assignment, I identified course outcomes 3 and 4 for this enhancement. I believe my completed work demonstrates progress toward both.

For outcome 3, I developed the rolling-average algorithm and considered the trade-offs between reducing unusual temperature fluctuations and responding quickly to actual changes. For outcome 4, I applied data structures, temperature-processing logic, and automated testing to improve the application.

My original outcome-coverage plan has not changed, and I intend to continue building on these skills during the remaining enhancement.

## Reflection on the Enhancement Process

One of my biggest challenges was figuring out how to handle unusual temperature readings without ignoring actual changes. I learned that even when an algorithm produces the correct calculations, it's important to consider how it responds to unexpected situations.

I also had to make sure the different parts of the thermostat could use the processed temperatures without adding unnecessary readings to the queue. Testing helped me work through these issues. All 24 automated tests passed, and I manually tested the simulation using temperature spikes, sustained changes, invalid inputs, and boundary values.

Although I haven't physically retested the Raspberry Pi, the simulation and automated tests helped me verify the enhanced temperature-processing logic. This experience gave me a better understanding of how algorithms, data structures, and careful testing can improve an existing application.

## Project Files

- [Original Thermostat Source Code](https://github.com/chrismgrey/chrismgrey.github.io/blob/main/artifacts/original/original.py)
- [Milestone Three Enhanced Code and Tests](https://github.com/chrismgrey/chrismgrey.github.io/tree/main/artifacts/milestone-three)
- [Milestone Three Narrative (Word Document)](./Milestone%20Three%20Narrative.docx)

[Return to ePortfolio Homepage](../)
