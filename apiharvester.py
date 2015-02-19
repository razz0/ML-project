"""API harvester module"""

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


def timerange(start_datetime, end_datetime, delta):
    '''
    Generate a time range

    >>> print [a.hour for a in timerange(datetime(2012, 2, 5), datetime(2012, 2, 5, 23, 59, 59), timedelta(hours=1))]
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
    '''
    current_datetime = start_datetime
    while current_datetime < end_datetime:
        yield current_datetime
        current_datetime += delta


class APIHarvester(object):
    """
    Harvester class for gathering data from FMI and HSL APIs
    """

    HSL_BASE = 'http://www.poikkeusinfo.fi/xml/v2/'
    FMI_BASE = 'http://data.fmi.fi/fmi-apikey/{apikey}/wfs'

    FMI_API_FILE = '../fmi_api.txt'
    FMI_DATA_FILE = '../data/fmi.json'
    HSL_DATA_FILE = '../data/hsl.json'

    FMI_FORECAST_PARAMS = {'request': 'getFeature', 'storedquery_id': 'fmi::forecast::hirlam::surface::point::simple', 'place': 'kaisaniemi,helsinki', 'timestep': 60}
    FMI_FORECAST_FIELDS = ['Temperature', 'WindSpeedMS', 'Precipitation1h']

    FMI_HISTORY_PARAMS = {'request': 'getFeature', 'storedquery_id': 'fmi::observations::weather::simple', 'place': 'kaisaniemi,helsinki', 'timestep': 60}
    FMI_HISTORY_FIELDS = ['t2m', 'ws_10min', 'r_1h']

    FMI_NAMESPACES = {'BsWfs': 'http://xml.fmi.fi/schema/wfs/2.0', 'wfs': "http://www.opengis.net/wfs/2.0"}

    def __init__(self, loglevel=logging.INFO, logfile='../harvester.log', apikey=None ):
        logging.basicConfig(filename=logfile, level=loglevel, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logging.info('Harvester initialized')

        if apikey:
            self.fmi_apikey = apikey
        else:
            with open(self.FMI_API_FILE, 'r') as f:
                self.fmi_apikey = f.read().replace('\n', '')

    def read_fmi_datafile(self):
        with open(self.FMI_DATA_FILE, 'r') as f:
            try:
                data = json.load(f)
                logging.info('Read %s FMI data objects' % len(data))
                return data
            except ValueError:
                logging.error('Unable to read %s' % self.FMI_DATA_FILE)
                return None

    def read_hsl_datafile(self):
        with open(self.HSL_DATA_FILE, 'r') as f:
            try:
                data = json.load(f)
                logging.info('Read %s HSL data objects' % len(data))
                return data
            except ValueError:
                logging.error('Unable to read %s' % self.HSL_DATA_FILE)
                return None

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
        :rtype : dict
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
                # print "%s - %s - %s" % (time, key, value)
                forecasts[time].update({key: value})

        #pprint.pprint(forecasts)
        logging.info('Received weather forecasts for {num} time instants'.format(num=len(forecasts)))

        return forecasts

    def fmi_observation(self, start_time, end_time, params=FMI_HISTORY_PARAMS):
        """
        Get weather observation data from FMI API. The API supports only short timespans (max 68h).
        :param start_time: starting date & time string (ISO8601)
        :param end_time: ending date & time string (ISO8601)
        :param params:
        """
        url = self.FMI_BASE.format(apikey=self.fmi_apikey)

        params.update({'starttime': start_time + 'Z', 'endtime': end_time + 'Z'})

        logging.info('Getting weather observations from {url} with parameters {params}'.format(url=url, params=params))

        result = requests.get(url, params=params)
        result_xml = result.text.encode('ascii', 'ignore')
        result_etree = etree.fromstring(result_xml)

        elements = result_etree.xpath('wfs:member/BsWfs:BsWfsElement', namespaces=self.FMI_NAMESPACES)

        observations = defaultdict(dict)

        if not len(elements):
            logging.warning('No weather elements found from output: %s' % result_xml)

        for elem in elements:
            time = elem.xpath('BsWfs:Time', namespaces=self.FMI_NAMESPACES)[0].text
            key = elem.xpath('BsWfs:ParameterName', namespaces=self.FMI_NAMESPACES)[0].text
            value = elem.xpath('BsWfs:ParameterValue', namespaces=self.FMI_NAMESPACES)[0].text
            if key in self.FMI_HISTORY_FIELDS:
                logging.debug("%s - %s - %s" % (time, key, value))
                observations[time].update({key: value})

        logging.info('Received weather observations for {num} time instants'.format(num=len(observations)))

        return observations

    def test_hsl(self):
        assert self.hsl_api(datetime(2010, 9, 17, 9, 0)) == 2
        assert self.hsl_api(datetime(2011, 9, 17, 9, 0)) == 4
        assert self.hsl_api(datetime(2015, 1, 29, 15, 15)) == 0
        print 'HSL OK'

    def harvest_hsl(self, harvest_start, harvest_end, delay=0.5):
        """
        Harvest HSL data and save it to json file. Safe for use by a single process at a time.
        :param harvest_start: date or datetime
        :param harvest_end: date or datetime
        :param delay: delay between API calls in seconds
        """
        data_hsl = self.read_hsl_datafile()

        for single_date in daterange(harvest_start, harvest_end):
            for hour in range(0, 24):
                instant = datetime(single_date.year, single_date.month, single_date.day, hour)
                datestr = instant.isoformat()
                if data_hsl.get(datestr) is None:
                    data_hsl.update({datestr: self.hsl_api(instant)})
                    time.sleep(delay)

        with open(self.HSL_DATA_FILE, 'w') as f:
            logging.info('Dumping %s objects of HSL data to %s' % (len(data_hsl), self.HSL_DATA_FILE))
            json.dump(data_hsl, f)

    def harvest_fmi(self, harvest_start, harvest_end):
        """
        Harvest FMI data and save it to json file.
        :param harvest_start: datetime
        :param harvest_end: datetime
        """
        data_fmi = self.read_fmi_datafile()

        if not all([t.isoformat() in data_fmi for t in
                    timerange(harvest_start, harvest_end, timedelta(hours=1))]):
            data_fmi.update(self.fmi_observation(harvest_start.isoformat(), harvest_end.isoformat()))
        else:
            logging.info('Time range beginning from %s already harvested' % (harvest_start))

        with open(self.FMI_DATA_FILE, 'w') as f:
            logging.info('Dumping %s objects of FMI data to %s' % (len(data_fmi), self.FMI_DATA_FILE))
            json.dump(data_fmi, f)


