import math, itertools, collections, time, pickle
from datetime import datetime
import iso8601

import json, pprint
import urllib
from lxml import etree

def hsl_api(when, debug=True):
  """
  Get disruption info from HSL API
  """
  HSL_BASE = 'http://www.poikkeusinfo.fi/xml/v2/'

  date_string = "%02d%02d%s%02d%02d" % (when.day, when.month, when.year, when.hour, when.minute)
  
  url = HSL_BASE + date_string

  if debug:
    print 'Getting disruptions from %s' % url

  api_response = urllib.urlopen(url)
  result_xml = api_response.read()
  result_etree = etree.fromstring(api_xml)

  if debug:
    print result_xml

  result_time = iso8601.parse_date(result_etree.get('time'))

  # Check dates because API returns current info with bad parameters
  assert result_time.date() == when.date()  

  return result_etree.get('valid')


#hsl_api(datetime.now())

