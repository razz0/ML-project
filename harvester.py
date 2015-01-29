from datetime import datetime
import iso8601

import json, pprint
import requests
from lxml import etree
from collections import defaultdict

class APIHarvester(object):
    """
    Harvest data from APIs
    """
  
    HSL_BASE = 'http://www.poikkeusinfo.fi/xml/v2/'
    
    FMI_BASE = 'http://data.fmi.fi/fmi-apikey/{apikey}/wfs'
    FMI_PARAMS = {'request': 'getFeature', 'storedquery_id': 'fmi::forecast::hirlam::surface::point::simple', 'place': 'kaisaniemi,helsinki', 'timestep': 60}
    FMI_API_FILE = '../fmi_api.txt'
    FMI_NAMESPACES = {'BsWfs': 'http://xml.fmi.fi/schema/wfs/2.0', 'wfs': "http://www.opengis.net/wfs/2.0"}
    FMI_WANTED_VALUES = ['Temperature', 'WindSpeedMS', 'Precipitation1h']
    
    def __init__(self, debug=False):
        self.debug = debug
        if self.debug:
          print('Harvester initialized')
          
        with open(self.FMI_API_FILE, 'r') as f:
          self.fmi_apikey = f.read().replace('\n', '')
  
    def hsl_api(self, when):
        """
        Get disruption info from HSL API
        """
        date_string = "%02d%02d%s%02d%02d" % (when.day, when.month, when.year, when.hour, when.minute)
        
        url = self.HSL_BASE + date_string
    
        if self.debug:
          print('Getting disruptions from %s') % url
    
        result = requests.get(url)
        result_xml = result.text.encode('ascii', 'ignore')
        result_etree = etree.fromstring(result_xml)
    
        result_time = iso8601.parse_date(result_etree.get('time'))
        
        # Check that dates match since API returns current disruptions with invalid parameters
        assert result_time.date() == when.date()
    
        disruptions = result_etree.get('valid')
        
        if self.debug:
          print('Got %s disruptions') % disruptions
          
        return int(disruptions)
  
    def fmi_forecast(self, params=FMI_PARAMS):
        """
        Get Forecast info from HSL API
        """
        url = self.FMI_BASE.format(apikey=self.fmi_apikey)
        
        if self.debug:
          print('Getting forecast from {url} with parameters {params}').format(url=url, params=params)
    
        result = requests.get(url, params=params)
        result_xml = result.text.encode('ascii', 'ignore')
        result_etree = etree.fromstring(result_xml)
        
        elements = result_etree.xpath('wfs:member/BsWfs:BsWfsElement', namespaces=self.FMI_NAMESPACES)
        
        forecasts = defaultdict(dict)
        
        for elem in elements:
            time = elem.xpath('BsWfs:Time', namespaces=self.FMI_NAMESPACES)[0].text
            key = elem.xpath('BsWfs:ParameterName', namespaces=self.FMI_NAMESPACES)[0].text
            value = elem.xpath('BsWfs:ParameterValue', namespaces=self.FMI_NAMESPACES)[0].text
            if key in self.FMI_WANTED_VALUES:
                print "%s - %s - %s" % (time, key, value)
                forecasts[time].update({key: value})
            
        #pprint.pprint(forecasts)
        if self.debug:
            print 'Received forecasts for {num} time instants'.format(num=len(forecasts))
    

    def test_HSL(self):
        assert harvester.hsl_api(datetime(2010, 9, 17, 9, 0)) == 2
        assert harvester.hsl_api(datetime(2011, 9, 17, 9, 0)) == 4
        assert harvester.hsl_api(datetime(2015, 1, 29, 15, 15)) == 0
        print 'HSL OK'
        

        

harvester = APIHarvester(debug=True)

#harvester.test_HSL()

harvester.fmi_forecast()

