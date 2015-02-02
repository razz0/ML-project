from datetime import datetime, timedelta, date
import time
import iso8601

import json, pprint
import logging
import requests
from lxml import etree
from collections import defaultdict

def daterange(start_date, end_date):
    '''
    Taken from http://stackoverflow.com/a/1060330/1816143
    '''
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)


class APIHarvester(object):
    """
    Harvest data from APIs
    """
  
    HSL_BASE = 'http://www.poikkeusinfo.fi/xml/v2/'
    FMI_BASE = 'http://data.fmi.fi/fmi-apikey/{apikey}/wfs'

    FMI_API_FILE = '../fmi_api.txt'
    FMI_DATA_FILE = '../data_fmi.json'
    HSL_DATA_FILE = '../data_hsl.json'

    FMI_FORECAST_PARAMS = {'request': 'getFeature', 'storedquery_id': 'fmi::forecast::hirlam::surface::point::simple', 'place': 'kaisaniemi,helsinki', 'timestep': 60}
    FMI_FORECAST_FIELDS = ['Temperature', 'WindSpeedMS', 'Precipitation1h']

    FMI_HISTORY_PARAMS = {'request': 'getFeature', 'storedquery_id': 'fmi::observations::weather::simple', 'place': 'kaisaniemi,helsinki', 'timestep': 60}
    FMI_HISTORY_FIELDS = ['t2m', 'ws_10min', 'r_1h']

    FMI_NAMESPACES = {'BsWfs': 'http://xml.fmi.fi/schema/wfs/2.0', 'wfs': "http://www.opengis.net/wfs/2.0"}

    def __init__(self, loglevel=logging.INFO, logfile='../harvester.log', ):
        logging.basicConfig(filename=logfile, level=loglevel, format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info('Harvester initialized')
          
        with open(self.FMI_API_FILE, 'r') as f:
            self.fmi_apikey = f.read().replace('\n', '')

        self.data_fmi = {}
        self.data_hsl = {}

    def hsl_api(self, when):
        """
        Get disruption info from HSL API
        :param when: datetime
        :rtype : int
        """
        date_string = "%02d%02d%s%02d%02d" % (when.day, when.month, when.year, when.hour, when.minute)
        
        url = self.HSL_BASE + date_string
    
        logging.info('Getting disruptions from %s' % url)
    
        result = requests.get(url)
        result_xml = result.text.encode('ascii', 'ignore')
        result_etree = etree.fromstring(result_xml)
    
        result_time = iso8601.parse_date(result_etree.get('time'))
        
        # Check that dates match since API returns current disruptions with invalid parameters
        assert result_time.date() == when.date()
    
        disruptions = result_etree.get('valid')
        
        logging.info('Got %s disruptions' % disruptions)
          
        return int(disruptions)
  
    def fmi_forecast(self, params=FMI_FORECAST_PARAMS):
        """
        Get weather forecast from FMI API
        """
        url = self.FMI_BASE.format(apikey=self.fmi_apikey)
        
        logging.info('Getting forecast from {url} with parameters {params}'.format(url=url, params=params))
    
        result = requests.get(url, params=params)
        result_xml = result.text.encode('ascii', 'ignore')
        result_etree = etree.fromstring(result_xml)
        
        elements = result_etree.xpath('wfs:member/BsWfs:BsWfsElement', namespaces=self.FMI_NAMESPACES)
        
        forecasts = defaultdict(dict)
        
        for elem in elements:
            time = elem.xpath('BsWfs:Time', namespaces=self.FMI_NAMESPACES)[0].text
            key = elem.xpath('BsWfs:ParameterName', namespaces=self.FMI_NAMESPACES)[0].text
            value = elem.xpath('BsWfs:ParameterValue', namespaces=self.FMI_NAMESPACES)[0].text
            if key in self.FMI_FORECAST_FIELDS:
                print "%s - %s - %s" % (time, key, value)
                forecasts[time].update({key: value})
            
        #pprint.pprint(forecasts)
        logging.info('Received weather forecasts for {num} time instants'.format(num=len(forecasts)))

        return forecasts

    def fmi_observation(self, start_time, end_time, params=FMI_HISTORY_PARAMS):
        """
        Get weather observation data from FMI API
        :param start_time: starting date & time string (ISO8601)
        :param end_time: ending date & time string (ISO8601)
        :param params:
        """
        url = self.FMI_BASE.format(apikey=self.fmi_apikey)

        params.update({'starttime': start_time, 'endtime': end_time})

        logging.info('Getting weather observations from {url} with parameters {params}'.format(url=url, params=params))

        result = requests.get(url, params=params)
        result_xml = result.text.encode('ascii', 'ignore')
        result_etree = etree.fromstring(result_xml)

        elements = result_etree.xpath('wfs:member/BsWfs:BsWfsElement', namespaces=self.FMI_NAMESPACES)

        observations = defaultdict(dict)

        for elem in elements:
            time = elem.xpath('BsWfs:Time', namespaces=self.FMI_NAMESPACES)[0].text
            key = elem.xpath('BsWfs:ParameterName', namespaces=self.FMI_NAMESPACES)[0].text
            value = elem.xpath('BsWfs:ParameterValue', namespaces=self.FMI_NAMESPACES)[0].text
            if key in self.FMI_HISTORY_FIELDS:
                print "%s - %s - %s" % (time, key, value)
                observations[time].update({key: value})

        logging.info('Received weather observations for {num} time instants'.format(num=len(observations)))

        return observations

    def test_hsl(self):
        assert self.hsl_api(datetime(2010, 9, 17, 9, 0)) == 2
        assert self.hsl_api(datetime(2011, 9, 17, 9, 0)) == 4
        assert self.hsl_api(datetime(2015, 1, 29, 15, 15)) == 0
        print 'HSL OK'

    def harvest(self, harvest_start, harvest_end, delay=2):
        """
        Harvest actual data and save it to json files.
        """
        with open(self.FMI_DATA_FILE, 'r') as f:
            try:
                self.data_fmi = json.load(f)
                logging.info('Read %s FMI data objects' % len(self.data_fmi))
            except ValueError:
                logging.error('Unable to read %s' % self.FMI_DATA_FILE)

        with open(self.HSL_DATA_FILE, 'r') as f:
            try:
                self.data_hsl = json.load(f)
                logging.info('Read %s HSL data objects' % len(self.data_hsl))
            except ValueError:
                logging.error('Unable to read %s' % self.HSL_DATA_FILE)

        for single_date in daterange(harvest_start, harvest_end):
            for hour in range(0, 23):
                instant = datetime(single_date.year, single_date.month, single_date.day, hour)
                datestr = instant.isoformat()
                # self.data_fmi.update()
                if self.data_hsl.get(datestr) is None:
                    self.data_hsl.update({datestr: self.hsl_api(instant)})
                    time.sleep(delay)

        with open(self.FMI_DATA_FILE, 'w') as f:
            logging.info('Dumping %s objects of FMI data to %s' % (len(self.data_fmi), self.FMI_DATA_FILE))
            json.dump(self.data_fmi, f)

        with open(self.HSL_DATA_FILE, 'w') as f:
            logging.info('Dumping %s objects of HSL data to %s' % (len(self.data_hsl), self.HSL_DATA_FILE))
            json.dump(self.data_hsl, f)


#################################

harvester = APIHarvester()

#harvester.test_hsl()
#harvester.fmi_forecast()
pprint.pprint(harvester.fmi_observation(datetime(2010, 9, 17, 9, 0).isoformat(), datetime(2010, 9, 17, 18, 0).isoformat()))

#harvester.harvest(date(2008, 1, 1), date(2008, 12, 31), delay=1)

