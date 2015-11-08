"""Fix timezones to UTC in data files"""

from datetime import timedelta, datetime
import json
import arrow
from dateutil import tz
import shutil

import iso8601
import pytz

from .apiharvester import APIHarvester

harvester = APIHarvester()

fmi_data = harvester.read_fmi_datafile()
hsl_data = harvester.read_hsl_datafile()

print('FMI data length: %s' % (len(fmi_data)))
print('HSL data length: %s' % (len(hsl_data)))

helsinki = tz.gettz('Europe/Helsinki')
utc = tz.gettz('UTC')
now = datetime.now(helsinki)

print('Making backups')
shutil.copyfile(harvester.FMI_DATA_FILE, harvester.FMI_DATA_FILE + "." + now.isoformat())
shutil.copyfile(harvester.HSL_DATA_FILE, harvester.HSL_DATA_FILE + "." + now.isoformat())

new_hsl = {}
new_fmi = {}

for timestamp, value in hsl_data.items():
    time = iso8601.parse_date(timestamp, default_timezone=helsinki)
    new_time = time.astimezone(utc)
    new_timestamp = new_time.isoformat()

    new_hsl.update({new_timestamp: value})

print('Saving new HSL data file')
print('Length: %s' % (len(new_hsl)))
print('Format: %s --> %s' % (timestamp, new_timestamp))
with open(harvester.HSL_DATA_FILE, 'w') as f:
    json.dump(new_hsl, f)

for timestamp, value in fmi_data.items():
    time = iso8601.parse_date(timestamp, default_timezone=utc)
    new_time = time.astimezone(utc)
    new_timestamp = new_time.isoformat()

    new_fmi.update({new_timestamp: value})

    if timestamp == new_timestamp:
        print(time)
        print(new_time.isoformat())
        break

print('Saving new FMI data file')
print('Length: %s' % (len(new_fmi)))
print('Format: %s --> %s' % (timestamp, new_timestamp))
with open(harvester.FMI_DATA_FILE, 'w') as f:
    json.dump(new_fmi, f)
