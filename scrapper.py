#! /usr/bin/env python

import requests
import json
import os
import time
import argparse
from datetime import datetime
import copy 
import gzip

MAP_URL = 'https://www.realtor.ca/Residential/Map.aspx'
API_URL = 'https://api2.realtor.ca/Listing.svc/PropertySearch_Post'

# see https://github.com/Froren/realtorca

priceTiers = [0, 25000, 50000, 75000, 100000, 125000, 150000, 175000, 200000, 225000, 250000, 275000, 300000, 325000, 350000, 375000, 400000, 425000, 450000, 475000, 500000, 550000, 600000, 650000, 700000, 750000, 800000, 850000, 900000, 950000, 1000000, 1100000, 1200000, 1300000, 1400000, 1500000, 1600000, 1700000, 1800000, 1900000, 2000000, 2500000, 3000000, 4000000, 5000000, 7500000, 10000000];

def get_all_records_realtor(request_form):
  """
  Retrieve all records split between several pages
  """
  _max_records_per_page=200
  headers = {'user-agent': 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36'}
  
  form_base = {'CultureId': 1, 'ApplicationId': 1, 'PropertySearchTypeId': 1,'TransactionTypeId': 2, 'Version':7.0,
               'CurrentPage':1 ,   'RecordsPerPage': _max_records_per_page , 'ZoomLevel':13  }
  form_base.update(request_form)
  resp=[]

  while True:
    http_resp=requests.post(API_URL, data=form_base, headers=headers)
    prop = http_resp.json()

    if prop['ErrorCode']['Id'] == 200: # success
      res = prop['Results']

      resp.extend(res) # dump all records for now

      if prop['Paging']['CurrentPage'] < prop['Paging']['TotalPages']:
        form_base['CurrentPage'] = prop['Paging']['CurrentPage']+1
      else:
        break
    else:
      print(http_resp)
      break

  return resp


def parse_options():
  parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                              description='scrapper')

  parser.add_argument('dump_loc',
                  default="/home/vfonov/realtor",
                  help='Output directory location' )
  options = parser.parse_args()

  return options


if __name__ == '__main__':
  options=parse_options()
  dump_loc=options.dump_loc

  if not os.path.exists(dump_loc):
    os.makedirs(dump_loc)

  # montreal island
  ROIS_all = \
  [{
    "LongitudeMin": -73.761215,
    "LatitudeMin": 45.506486,
    "LongitudeMax": -73.621943,
    "LatitudeMax": 45.587327
  },
  {
    "LongitudeMin": -73.603085,
    "LatitudeMin": 45.590301,
    "LongitudeMax": -73.535887,
    "LatitudeMax": 45.634201
  },
  {
    "LongitudeMin": -73.677626,
    "LatitudeMin": 45.450772,
    "LongitudeMax": -73.59423,
    "LatitudeMax": 45.516608
  },
  {
    "LongitudeMin": -73.944335,
    "LatitudeMin": 45.466779,
    "LongitudeMax": -73.855024,
    "LatitudeMax": 45.520994
  },
  {
    "LongitudeMin": -73.724573,
    "LatitudeMin": 45.427612,
    "LongitudeMax": -73.629076,
    "LatitudeMax": 45.473339
  },
  {
    "LongitudeMin": -73.665984,
    "LatitudeMin": 45.414591,
    "LongitudeMax": -73.569647,
    "LatitudeMax": 45.4577
  },
  {
    "LongitudeMin": -73.612422,
    "LatitudeMin": 45.504955,
    "LongitudeMax": -73.559226,
    "LatitudeMax": 45.541598
  },
  {
    "LongitudeMin": -73.635305,
    "LatitudeMin": 45.437482,
    "LongitudeMax": -73.537162,
    "LatitudeMax": 45.498302
  },
  {
    "LongitudeMin": -73.569679,
    "LatitudeMin": 45.531435,
    "LongitudeMax": -73.503934,
    "LatitudeMax": 45.615885
  },
  {
    "LongitudeMin": -73.654334,
    "LatitudeMin": 45.575994,
    "LongitudeMax": -73.601668,
    "LatitudeMax": 45.629861
  },
  {
    "LongitudeMin": -73.626988,
    "LatitudeMin": 45.50406,
    "LongitudeMax": -73.590207,
    "LatitudeMax": 45.527784
  },
  {
    "LongitudeMin": -73.947552,
    "LatitudeMin": 45.440425,
    "LongitudeMax": -73.751683,
    "LatitudeMax": 45.517106
  },
  {
    "LongitudeMin": -73.620694,
    "LatitudeMin": 45.612588,
    "LongitudeMax": -73.476198,
    "LatitudeMax": 45.703798
  },
  {
    "LongitudeMin": -73.621536,
    "LatitudeMin": 45.525643,
    "LongitudeMax": -73.548959,
    "LatitudeMax": 45.581926
  },
  {
    "LongitudeMin": -73.774171,
    "LatitudeMin": 45.460662,
    "LongitudeMax": -73.651026,
    "LatitudeMax": 45.532326
  },
  {
    "LongitudeMin": -73.629631,
    "LatitudeMin": 45.566387,
    "LongitudeMax": -73.563944,
    "LatitudeMax": 45.611148
  },
  {
    "LongitudeMin": -73.599367,
    "LatitudeMin": 45.435,
    "LongitudeMax": -73.531894,
    "LatitudeMax": 45.475067
  },
  {
    "LongitudeMin": -73.606838,
    "LatitudeMin": 45.486744,
    "LongitudeMax": -73.517977,
    "LatitudeMax": 45.539899
  },
  {
    "LongitudeMin": -73.648533,
    "LatitudeMin": 45.523342,
    "LongitudeMax": -73.586299,
    "LatitudeMax": 45.585464
  },
  { #Longueuil
     "LongitudeMin":-73.52919,
     "LatitudeMin":45.43298,
     "LongitudeMax":-73.33898,
     "LatitudeMax":45.58895
  },
  { #Saint-Lambert
     "LongitudeMin":-73.52512,
     "LatitudeMin":45.47624,
     "LongitudeMax":-73.47452,
     "LatitudeMax":45.51925
  }
  ]

  forms = [ {
     # triplexes
    'BuildingTypeId':3,
    'PriceMin':0,
    'PriceMax':0
    },
    { # duplexes
    'BuildingTypeId':2,
    'PriceMin':0,
    'PriceMax':0
    },
    { # quadruplexes
    'BuildingTypeId':19,
    'PriceMin':0,
    'PriceMax':0
    },
    { # houses
    'BuildingTypeId':1,
    'PriceMin':0,
    'PriceMax':0
    },
    { # town houses
    'BuildingTypeId':16,
    'PriceMin':0,
    'PriceMax':0
    },
    # condos
    {
    'BuildingTypeId':17,
    'PriceMin':0,
    'PriceMax':100000
    },
    {
    'BuildingTypeId':17,
    'PriceMin':100000,
    'PriceMax':200000
    },
    {
    'BuildingTypeId':17,
    'PriceMin':200000,
    'PriceMax':300000
    },
    {
    'BuildingTypeId':17,
    'PriceMin':300000,
    'PriceMax':500000
    },
    {
    'BuildingTypeId':17,
    'PriceMin':500000,
    'PriceMax':0
    }
  ]

  ts=time.time()
  time_stamp = datetime.fromtimestamp(ts).isoformat()

  # ADD new ROI
  all_results={}
  for r in ROIS_all:
    for f in forms:
      f.update(r)
      res=get_all_records_realtor(f)
      #print(len(res))
      all_results.update( { i['MlsNumber']:i for i in res } )

  all_results_dump = {
    'ts':ts,
    'results': [ i[1] for i in all_results.items()]
  }

  with gzip.open(dump_loc+os.sep+'all_{}.json.gz'.format(time_stamp),'wt') as f:
    json.dump(all_results_dump,f)
