

# Milestone Two: Software Design and Engineering



## Artifact Description



For this enhancement, I selected the Raspberry Pi thermostat that I originally developed during CS-350 Emerging Systems Architectures and Technologies in 2026. The application uses Python and a Raspberry Pi 4 to monitor temperature, manage heating and cooling modes, control LEDs, display information on an LCD, and communicate with a server through a serial connection.



## Reason for Selection and Enhancements



I chose this project for my ePortfolio because it was one of my more involved programming assignments and gave me an opportunity to demonstrate how I could improve an existing application. While the original thermostat worked, most of its control logic and hardware operations were combined in one Python file, making it difficult to test without the physical hardware.



My main improvement was separating the thermostat's control logic into its own module while keeping the hardware operations in the main application. I also added temperature validation, setpoint limits, improved error handling, and hardware cleanup. Creating a desktop simulation and automated unit tests allowed me to verify the thermostat's functionality without needing the Raspberry Pi. These changes demonstrate my ability to organize code, troubleshoot problems, and make an existing application easier to maintain and expand.



## Course Outcomes



In my Module One assignment, I identified course outcomes 2, 3, and 4 for this enhancement. I believe my completed work demonstrates progress toward each of them.



For outcome 2, I documented my changes and explained my design decisions through the code review and supporting documentation. For outcome 3, I evaluated the original design and considered the trade-offs involved in separating hardware operations from the main control logic. For outcome 4, I applied modular software design, hardware simulation, and automated testing to improve the application.



My original outcome-coverage plan has not changed. I intend to continue demonstrating these skills while completing the remaining enhancements.



## Reflection on the Enhancement Process



One of the biggest things I learned was that having a working program doesn't necessarily mean the code cannot be improved. Organizing the application into separate components required me to think more carefully about how everything interacted.



My biggest challenge was preserving the thermostat's original functionality while changing its structure. I also spent considerable time reviewing the code, troubleshooting issues, and improving how the application handled invalid readings and hardware errors. Being able to run simulations and automated tests made that process much easier.



Although I wasn't able to physically retest the Raspberry Pi, the simulation and testing helped me verify the core functionality. This experience gave me a better understanding of why maintainability, testing, and careful code review are important parts of software development.



## Project Files



- [Original Thermostat Source Code](https://github.com/chrismgrey/chrismgrey.github.io/blob/main/artifacts/original/original.py)

- [Milestone Two Enhanced Code and Tests](https://github.com/chrismgrey/chrismgrey.github.io/tree/main/artifacts/milestone-two)

- [Milestone Two Narrative (Word Document)](./Milestone%20Two%20Narrative.docx)



[Return to ePortfolio Homepage](../)



