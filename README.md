# InreachToOGN
This script grabs Inreach location data from [Inreachuser.csv](https://github.com/DavisChappins/InreachToOGN/blob/main/Inreachuser.csv) in this repository and uploads it to the OGN to be viewable on OGN sites like https://glidertracker.org/. For more information about the OGN see http://wiki.glidernet.org/.  
It's currently running on my local machine 24 hrs a day, 7 days a week.
  
## How can I add my Inreach?
First, [enable mapshare](https://support.garmin.com/en-US/?faq=EMrPa9gUgU1ZNM3LmfGneA) then fill out the google form at https://forms.gle/WN3YLVJvL5pp7feq6  
You will need:
* A share.garmin.com user name
* The N number or ICAO id of your aircraft
* Your name

## How can I tell if it is running?
After turning on your Inreach device, your position may take 5-15 minutes to appear. If your position is not valid or is older than 30 minutes at share.garmin.com you will not appear. Ensure your username and aircraft info is in the [Inreachuser.csv](https://github.com/DavisChappins/InreachToOGN/blob/main/Inreachuser.csv) file. The csv file is updated by filling out [this google form](https://forms.gle/WN3YLVJvL5pp7feq6  ). If you have recently filled out the form it may take a short amount of time for your info to be added.  
The script connects to http://glidern2.glidernet.org:14501/ ctrl+f for "Inreach" to verify the script is connected and running.  

## What does it look like on a map?
Go to https://glidertracker.org/ and find your location. Inreach position data is pushed to the OGN as an "unknown object" and will appear as a google maps type pin. Inreach position data will be 5-15 minutes behind your actual location but will update every 10 minutes.  
See below for an example, GW aircraft from FLARM (red) and GW Inreach position (blue).
![Inreach on glidertracker.org](https://github.com/DavisChappins/InreachToOGN/blob/main/Images/GW_Inreach.jpg?raw=true)

## How does this script work?
Every 3 minutes, this script parses the list of share.garmin.com Inreach positions contained in Inreachuser.csv. If a position is found to be within the last 30 minutes, that position, timestamp, altitude, velocity, and heading are transmitted to the OGN servers to be displayed on any website that subscribes to OGN data. Inreach positions are transmitted as an "unknown" data type in order to not overwrite the "glider" data type. Some websites may reject "unknown" objects. Inreachuser.csv contains your ICAO hex code so the same information that you entered at http://ddb.glidernet.org/ is carried over and displayed on your Inreach position.
