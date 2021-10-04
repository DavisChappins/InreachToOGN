# InreachToOGN
This script grabs Inreach location data and uploads it to the OGN to be viewable on OGN sites like glidertracker.org  
It's running from 10a to 8p daily AZ time.
  
## How do I get added?
First, go to https://support.garmin.com/en-US/?faq=EMrPa9gUgU1ZNM3LmfGneA and enable mapshare, set mapshare to be public.  
Second, either create a pull request to update user.csv or email davis.chappins@gmail.com (me) with a your share.garmin user name. I will need: user name, N number or ICAO id of your aircraft, and a human readable name.  
For Example, if your shared position is available at https://share.garmin.com/share/z15 then "z15" is your user name.  


## How can I tell it is running?
The script connects to http://glidern2.glidernet.org:14501/ ctrl+f for "Inreach" to verify the script is connected and running.  
Your position may take 5-15 minutes to appear. If your position is not valid or is older than 30 minutes at share.garmin.com you will not appear.
