# InreachToOGN
This script grabs Inreach location data and uploads it to the OGN to be viewable on OGN sites like https://glidertracker.org/   
It's currently running on my local machine from 10a to 8p daily AZ time, 7 days a week.
  
## How do I get added?
Fill out the google form at https://forms.gle/WN3YLVJvL5pp7feq6  
You will need:
* A share.garmin user name
* The N number or ICAO id of your aircraft
* Your name

## How can I tell if it is running?
After turning on your Inreach device, your position may take 5-15 minutes to appear. If your position is not valid or is older than 30 minutes at share.garmin.com you will not appear. Ensure your username and aircraft info is in the [user.csv](https://github.com/DavisChappins/InreachToOGN/blob/main/user.csv) file. If you have recently filled out the form it may take a short amount of time for your info to be added.  
The script connects to http://glidern2.glidernet.org:14501/ ctrl+f for "Inreach" to verify the script is connected and running.  

## What does it look like on the map?
Go to https://glidertracker.org/ and find your location. Inreach position data is pushed to the OGN as an "unknown object" and will appear as a google maps type pin. Inreach position data will be 5-15 minutes behind your actual location but will update every 10 minutes.  
See below for an example, GW aircraft from FLARM (red) and GW Inreach position (blue).
![Inreach on glidertracker.org](https://github.com/DavisChappins/InreachToOGN/blob/main/Images/GW_Inreach.jpg?raw=true)
