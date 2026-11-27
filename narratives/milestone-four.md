# Milestone Four: Databases

## Artifact Description

For Milestone Four, I continued improving the Raspberry Pi thermostat I originally developed during CS-350. I selected this same artifact for all three enhancement categories in my CS-499 capstone so I could build on my previous work and demonstrate different areas of computer science through one application.

In Milestone Two, I focused on improving the application's structure, and in Milestone Three, I enhanced how it processes temperature readings. For this final enhancement, I added SQLite database functionality to store temperature readings and thermostat setting changes. This allows the application to maintain historical information between sessions rather than only working with its current readings and settings.

## Reason for Selecting the Artifact

I chose to continue developing this project for my ePortfolio because it gave me an opportunity to expand an existing application while demonstrating different programming skills. Before this enhancement, the thermostat could display its current temperature and settings, but it did not have a way to save that information for later use. Adding a database was a practical way to address that limitation.

My main improvement was creating an SQLite database with separate tables for temperature readings and thermostat setting changes. I added methods to retrieve historical readings, filter them by date, and calculate minimum, maximum, and average temperatures. I also integrated the database into both the desktop simulation and Raspberry Pi application while preserving the functionality developed in my previous milestones.

These improvements demonstrate my ability to design and work with databases, write SQL queries, and integrate new functionality into an existing application. I also incorporated input validation, parameterized queries, and error handling to help maintain the accuracy and integrity of the stored information.

## Course Outcomes

In my Module One assignment, I identified course outcomes 4 and 5 for this enhancement. I believe my completed work demonstrates progress toward both.

For outcome 4, I designed and integrated an SQLite database to store and retrieve historical thermostat information. I created database tables, developed SQL queries to retrieve and analyze temperature readings, and used automated testing to verify the functionality. These improvements demonstrate my ability to apply database development techniques to an existing application.

For outcome 5, I incorporated input validation, parameterized SQL queries, database constraints, and error handling to help protect the accuracy and integrity of the stored information. These practices also help reduce potential security risks and prevent invalid data from being recorded.

My original outcome-coverage plan has not changed. The completed database enhancement demonstrates the skills I planned to address in both database development and secure coding.

## Reflection on the Enhancement Progress

One of my biggest challenges was integrating the database without interfering with the thermostat's existing functionality. I needed to make sure the application saved accepted temperature readings without recording duplicate cached readings or unusual temperatures that had not been confirmed. This required me to consider how the database would interact with the temperature-processing logic I developed in Milestone Three.

I also learned how important it is to handle timestamps and database queries consistently. During testing, I found that timestamp precision could affect which records were returned when filtering readings by date. Working through this issue helped me better understand how small details in database design can affect the accuracy of retrieved information.

Testing was an important part of this enhancement. All 47 automated tests passed, and I manually verified that the simulation could save and retrieve information after restarting. Although I haven't physically retested the Raspberry Pi, the automated tests and simulated hardware interactions helped me verify the database integration.

This enhancement gave me a better understanding of how database design, data validation, and careful testing can make an existing application more useful and reliable.

## Project Files

- [Original Thermostat Source Code](https://github.com/chrismgrey/chrismgrey.github.io/blob/main/artifacts/original/original.py)
- [Milestone Four Enhanced Code and Tests](https://github.com/chrismgrey/chrismgrey.github.io/tree/main/artifacts/milestone-four)
- [Milestone Four Narrative (Word Document)](./Milestone%20Four%20Narrative.docx)

[Return to ePortfolio Homepage](../)
