#! /usr/bin/env python
import json
import os
import time
import glob
import argparse
import csv
import sqlite3
import gzip
from functools import reduce
from datetime import datetime,date

def convert_surface(val):
  # TODO: handle different units
  # detect irregular sizes
  reg=True
  val=val.lower()

  if val.find('irr')!=-1:
    val=val.replace('irr','')
    reg=False

  v=val.split(' ')
  _units=None 
  if len(v)==2:
    meas,units=v
    if units=='sqft': 
      _units=1.0
    elif units=='m2':
      _units=10.764
    elif units=='hec':
      _units=100*100*10.764
    val=meas

  if val.find('x') != -1:
    m=val.split('x')[0:2]

    if m[0].find('ft') != -1:
      _units=10.764
      m[0]=m[0].split('ft')[0]
      m[1]=m[1].split('ft')[0]
    val=float(m[0])*float(m[1])
  else:
    val=float(val)

  if _units is not None:
    return val*_units
  elif val<200: # probably m^2
    return val*10.764
  else:# probably square feet
    return val


def convert_linear(val):
  val=val.lower()
  # check if two parts
  vv=val.split(',')
  if len(vv)>1: # have inches
    val=vv[0]
    #ignore inches for now

  v=val.split(' ')
  _units=1 # sqft

  if len(v)>=2:
    meas=v[0]
    units=v[1]
    if units=='ft': 
      _units=1.0
    elif units=='m':
      _units=3.28084
    val=meas

  return float(val)*_units


def convert_price(val):
  """
  make it a float
  """
  fact=1.0
  if val.find('GST')!=-1:
    # there is GST and PST
    val=val.split('+')[0]
    fact=1.14975
  return float(val.replace('$','').replace(',',''))*fact


def convert_bedrooms(val):
  """
  decode the crap agents put in the descriptions
  """
  try:
    return int(val)
  except ValueError:
    # try to guess what it is
    val=val.split('+')[0]
    return reduce(lambda x, y: int(x)+int(y), [i for i in val.split('+')[0] if len(i)>0 and i!=' '])



def parse_options():
  parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                              description='Summarize date')

  parser.add_argument('dump_loc',
                  default="/home/vfonov/realtor",
                  help='Dump location' )

  parser.add_argument('db',
                  default="/home/vfonov/src/realtorca/real_estate.sqlite3",
                  help='SQLITE3 db' )
  options = parser.parse_args()

  return options

def get_one_broker_details(d):
  r={"broker_name":None, "broker_phone":None}
  # search for individual with phone
  for i in d.get('Individual', []):
    for p in i.get('Organization',{'Phones':[]}).get('Phones',[]):
         if p.get("PhoneType") == "Telephone":
            r['broker_name'] = i.get('Name',None)
            r['broker_phone'] = p.get("AreaCode", "") + " " + p.get("PhoneNumber","")
            break
  return r

if __name__ == '__main__':
  options=parse_options()
  if not options.dump_loc:
    print("Run with --help")
    exit(1)

  data=options.dump_loc
  conn = sqlite3.connect(options.db)

  # init tables
  cur = conn.cursor()

  cur.execute("create table if not exists file_stamp(fname text primary key,stamp )")
  cur.execute("""
  create table if not exists
  property(
    ts,mls integer,type,units integer,
    stories integer,bedrooms integer, bathrooms integer,
    area_interior real,area_exterior real,area_land real,
    frontage real,price real,parking integer,lat real,lng real,
    address,postal_code,photo_ts,broker_name,broker_phone,url
  )
  """)

  datasets=[]

  for i in glob.glob(data+os.sep+'*.json.gz'):
    # determine if already processed
    fname=os.path.basename(i).rsplit('.json.gz',1)[0]
    cur.execute("select count() from file_stamp where fname=?",(fname,))
    if cur.fetchone()[0]==0:
      with gzip.open(i,'r') as f:
        ds=json.load(f)
        #
        ts=date.fromtimestamp(float(ds['ts'])).isoformat()
        for d in ds['results']:
          bld=d['Building']
          #print(repr(bld))
          if 'PhotoChangeDateUTC' in d:
            photo_date=datetime.strptime(d['PhotoChangeDateUTC'], '%Y-%m-%d %H:%M:%S %p').strftime('%Y-%m-%d')
          else:
            photo_date=None

          r={
            "ts":       ts,
            "mls":      int(d['MlsNumber']),
            "type":     bld.get('Type',None),
            "units":    int(bld.get('UnitTotal',0)),
            "stories":  float(bld.get('StoriesTotal',0)),
            "bedrooms": convert_bedrooms(bld.get('Bedrooms',"0")),
            "bathrooms":int(bld.get('BathroomTotal',0)),
            "area_interior": convert_surface(bld.get('SizeInterior',"0 sqft")),
            "area_exterior":convert_surface(bld.get('SizeExterior',"0 sqft")),
            "area_land": convert_surface(d['Land'].get('SizeTotal','0 sqft')),
            "frontage" : convert_linear(d['Land'].get('SizeFrontage','0 ft')), 
            "price":    convert_price(d['Property']['Price']),
            "parking":  int(d['Property'].get('ParkingSpaceTotal',"0")),
            "lat":      float(d['Property']['Address']['Latitude']),
            "lng":      float(d['Property']['Address']['Longitude']),
            "address":  d['Property']['Address']['AddressText'],
            "postal_code": d['PostalCode'],
            "photo_ts": photo_date,
            "broker_name":None,
            "broker_phone":None,
            "url":d.get('AlternateURL',{}).get('DetailsLink',None)
            }
          r.update(get_one_broker_details(d))
          #datasets.append(r)
          cur.execute("""insert into property(ts,mls,type,units,
                      stories,bedrooms,bathrooms,
                      area_interior,area_exterior,area_land,
                      frontage,price,parking,lat,lng,
                      address,postal_code,photo_ts,broker_name,broker_phone,url) values (
                      :ts,:mls,:type,:units,
                      :stories,:bedrooms,:bathrooms,
                      :area_interior,:area_exterior,:area_land,
                      :frontage,:price,:parking,:lat,:lng,
                      :address,:postal_code,:photo_ts,:broker_name,:broker_phone,:url
            )""",r)

      # insert stamp
      cur.execute("insert into file_stamp(fname,stamp) values(:fname,:ts)",{"fname":fname,"ts":ts})
      print(fname)
  cur.execute("select count(*) from property")
  print("Found : {} records".format(cur.fetchone()[0]))
  #with open(out,'w') as f:
  #  json.dump(datasets,f,indent=1,sort_keys=True)
  # with open(out,'w') as f:
  #   w = csv.DictWriter(f, fieldnames=list(datasets[0].keys()))
  #   w.writeheader()
  #   for d in datasets:
  #     w.writerow(d)
  conn.commit()
