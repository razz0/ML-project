from datetime import datetime, timedelta, date
from apiharvester import APIHarvester, daterange
from predictor import *

#################################

harvester = APIHarvester()
#harvester = APIHarvester(loglevel=logging.DEBUG)

#harvester.test_hsl()
#harvester.fmi_forecast()
#pprint.pprint(harvester.fmi_observation(datetime(2010, 9, 17, 9, 0).isoformat(), datetime(2010, 9, 17, 18, 0).isoformat()))

for single_date in daterange(date(2010, 1, 1), date(2012, 12, 31)):
    harvester.harvest_fmi(datetime(single_date.year, single_date.month, single_date.day, 0, 0, 0),
                          datetime(single_date.year, single_date.month, single_date.day, 23, 59, 59))
    harvester.harvest_hsl(single_date, single_date + timedelta(days=1))

#year = 2010
#for day in [7, 11]:
#    harvester.harvest_fmi(datetime(year, 1, day), datetime(year, 1, day) + timedelta(days=1))
#    #harvester.harvest_hsl(date(year, 1, day), date(year, 1, day) + timedelta(days=1))

