#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup

import datetime
from datetime import datetime,date

import time
import sys
import os
import json
import argparse
import re
import sqlite3


script_match = re.compile(r'var dataLayer = ', re.MULTILINE | re.DOTALL)
scripts ={
    'bedrooms':re.compile(r'.*"numberbedrooms_s"\:"([0-9]+)".*', re.MULTILINE | re.DOTALL),
    'bathrooms':re.compile(r'.*"numberbathrooms_s"\:"([0-9]+)".*', re.MULTILINE | re.DOTALL),
    'petsallowed':re.compile(r'.*"petsallowed_s"\:"([0-9]+)".*', re.MULTILINE | re.DOTALL),
    'area': re.compile(r'.*"areainfeet_i"\:"([0-9]+)".*', re.MULTILINE | re.DOTALL),
    'parking': re.compile(r'.*"numberparkingspots_s"\:"([0-9]+)".*', re.MULTILINE | re.DOTALL),
    'furnished': re.compile(r'.*"furnished_s"\:"([0-9]+)".*', re.MULTILINE | re.DOTALL)
}


def parse_details(session, url):
    ### get details from AD url
    try:
        page = session.get(url) # Get the html data from the URL
    except (KeyboardInterrupt, SystemExit): # probably abort
        raise            
    except:
        return {}

    soup = BeautifulSoup(page.content, "html.parser")
    body = soup.body.find('div',{'data-fes-id':"VIP"})
    ad_info={}
    # get ad details
    try:
         ad_info['address']=body.find('span',{'itemprop':"address"}).text
    except (KeyboardInterrupt, SystemExit): # probably abort
        raise            
    except:
         ad_info['address']=''

    try:
        ad_info['price']=float(body.find('span',{'class': re.compile('currentPrice-.*')}).span['content'])
    except (KeyboardInterrupt, SystemExit): # probably abort
        raise            
    except:
        ad_info['price']=0.0

    try:
        ad_info['posted']=body.find('div',{'class': re.compile('datePosted-.*')}).time['datetime']
    except (KeyboardInterrupt, SystemExit): # probably abort
        raise            
    except:
        ad_info['posted']=''

    # ad_info['address']=''
    # ad_info['petsallowed']=''
    # ad_info['bathrooms']=''
    # ad_info['bedrooms']=''
    # ad_info['rentby']=''
    # ad_info['furnished']=''
    ad_info['latitude']=0.0
    ad_info['longitude']=0.0

    script = soup.find('script', text=script_match)
    if script:
        for i,j in scripts.items():
            try:
                ad_info[i]=j.search(str(script))[1]
            except:
                ad_info[i]=None
    else: #no script found
        for i,j in scripts.items():
            ad_info[i]=None
    
    try: 
        ad_info['latitude']=float(soup.find('meta',{'property':'og:latitude'})['content'])
        ad_info['longitude']=float(soup.find('meta',{'property':'og:longitude'})['content'])
    except (KeyboardInterrupt, SystemExit): # probably abort
        raise            
    except:
        pass

    # try:
    #     script=soup.find('script',text=script_match_bathrooms)
    #     if script:
    #         match = script_match_bathrooms.search(script.text)
    #         if match: ad_info['bathrooms']=match.group(1)
    # except:
    #     pass

    # try:
    #     script=soup.find('script',text=script_match_bedrooms)
    #     if script:
    #         match = script_match_bedrooms.search(script.text)
    #         if match: ad_info['bedrooms']=match.group(1)
    # except:
    #     pass

    # try:
    #     script=soup.find('script',text=script_match_rentby)
    #     if script:
    #         match = script_match_rentby.search(script.text)
    #         if match: ad_info['rentby']=match.group(1)
    # except:
    #     pass

    # try:
    #     script=soup.find('script',text=script_match_location)
    #     if script:
    #         match = script_match_location.search(script.text)
    #         if match: 
    #             ad_info['latitude']=match.group(1)
    #             ad_info['longitude']=match.group(2)
    #             #ad_info['address']=match.group(3)
    # except:
    #     pass

    # try:
    #     script=soup.find('script',text=script_match_furnished)
    #     if script:
    #         match = script_match_furnished.search(script.text)
    #         if match: 
    #             ad_info['furnished']=match.group(1)
    # except:
    #     pass

    return ad_info

def ParseAd(session, html):  # Parses ad html trees and sorts relevant data into a dictionary
    ts = date.today().isoformat()
    ad_info = {"ts":ts, "first_ts":ts}
    
    #description = html.find('div', {"class": "description"}).text.strip()
    #description = description.replace(html.find('div', {"class": "details"}).text.strip(), '')
    #print(description)
    try:
        ad_info["Title"] = html.find('a', {"class": "title"}).text.strip()
    except (KeyboardInterrupt, SystemExit): # probably abort
        raise            
    except:
        print('[Error] Unable to parse Title data.')
        ad_info["Title"] = None
        
    try:
        ad_info["Image"] = str(html.find('img')['src'])
    except (KeyboardInterrupt, SystemExit): # probably abort
        raise            
    except:
        print('[Error] Unable to parse Image data')
        ad_info["Image"] = None

    try:
        ad_info["Url"] = 'http://www.kijiji.ca' + html.get("data-vip-url")
    except (KeyboardInterrupt, SystemExit): # probably abort
        raise            
    except:
        print('[Error] Unable to parse URL data.')
        ad_info["Url"] = None
        
    try:
        ad_info["Details"] = html.find('div', {"class": "details"}).text.strip()
    except (KeyboardInterrupt, SystemExit): # probably abort
        raise            
    except:
        print('[Error] Unable to parse Details data.')
        ad_info["Details"] = None
        
    try:
        description = html.find('div', {"class": "description"}).text.strip()
        description = description.replace(ad_info["Details"], '')
        ad_info["Description"] = description
    except (KeyboardInterrupt, SystemExit): # probably abort
        raise            
    except:
        print('[Error] Unable to parse Description data.')    
        ad_info["Description"] = None
    
    if ad_info["Url"] is not None:
        ad_info.update(parse_details(session, ad_info["Url"]))

    return ad_info


def scrape(url, exclude_list, conn, table='rental'):  # Pulls page data from a given kijiji url and finds all ads on each page

    cur = conn.cursor()
    cur.execute(f"select count(*) from {table}")
    print(f"Starting with: {cur.fetchone()[0]} ads")

    # Initialize variables for loop
    #ad_dict = {}
    third_party_ad_ids = []
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'})
    pages_count=0
    null_results=0
    while url: 
        #print("scraping:{}".format(url))
        try:
            requests.utils.add_dict_to_cookiejar(session.cookies,{'siteLocale':'en_CA'})
            page = session.get(url) # Get the html data from the URL
        except (KeyboardInterrupt, SystemExit): # probably abort
            raise            
        except:
            print("[Error] Unable to load " + url)
            #sys.exit(1)
            break  # finished

        soup = BeautifulSoup(page.content, "html.parser")
        pages_count+=1
        #if not email_title: # If the email title doesnt exist pull it form the html data
        #    email_title = soup.find('div', {'class': 'message'}).find('strong').text.strip('"').strip("\n")
        #    email_title = toUpper(email_title)
        
        kijiji_ads = soup.find_all("div", {"class": "regular-ad"})  # Finds all ad trees in page html.
        
        third_party_ads = soup.find_all("div", {"class": "third-party"}) # Find all third-party ads to skip them
        for ad in third_party_ads:
            third_party_ad_ids.append(ad['data-ad-id'])
            
        exclude_list = toLower(exclude_list) # Make all words in the exclude list lower-case
        for ad in kijiji_ads:  # Creates a dictionary of all ads with ad id being the keys.
            title = ad.find('a', {"class": "title"}).text.strip() # Get the ad title
            ad_id = ad['data-listing-id'] # Get the ad id
            if not [False for match in exclude_list if match in title.lower()]: # If any of the title words match the exclude list then skip
                cur.execute(f'select count(*) from {table} where id=?',(ad_id,))

                if cur.fetchone()[0]>0: # update timestamp
                    cur.execute(f"update {table} set ts=? where id=?",(date.today().isoformat(), ad_id) )
                elif (ad_id not in third_party_ad_ids) : # Skip third-party ads
                    ad_dict = ParseAd(session, ad) # Parse data from ad
                    if 'bedrooms' not in ad_dict or ad_dict['bedrooms']=='': 
                        null_results+=1
                    else:
                        filter_and_insert(ad_id, ad_dict, cur, table)
        
        url = soup.find('a', {'title':'Next'})
        if url is not None:
            url = 'https://www.kijiji.ca' + url['href']
        else:
            url = soup.find('a', {'title':'Suivante'})
            if url is not None:
               url = 'https://www.kijiji.ca' + url['href']
        #print("next url="+repr(url))
    cur.execute(f"select count(*) from {table}")
    print("Finished with: {} ads, processed {} pages {} null results".format(cur.fetchone()[0],pages_count,null_results))

            
def toLower(input_list): # Rturns a given list of words to lower-case words
    output_list = list()
    for word in input_list:
        output_list.append(word.lower())
    return output_list

def toUpper(title): # Makes the first letter of every word upper-case
    new_title = list()
    title = title.split()
    for word in title:
        new_word = ''
        new_word += word[0].upper()
        if len(word) > 1:
            new_word += word[1:]
        new_title.append(new_word)
    return ' '.join(new_title)

def parse_options():
  parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                              description='KiJiJi scrapper')

  parser.add_argument('url',
                  help='Scrap this kijiki url' )
#   parser.add_argument('output',
#                   help='Keep results in this .json file' )

  parser.add_argument('--db',
                  default="property.sqlite3",
                  help='SQLITE3 db' )

  parser.add_argument('--table',
                  default="rental",
                  help='Table to hold entries' )

  parser.add_argument('--import_json',
                  default=None,
                  help="Import data from json dump, don't scrape" )


  parser.add_argument('--exclude',
                  help='Exclude list' )

  options = parser.parse_args()

  return options

def import_json(src, conn, table='rental'):
    cur=conn.cursor()
    cur.execute(f"select count(*) from {table}")
    print(f"Starting with: {cur.fetchone()[0]} ads")
    with open(src,'r') as f:
        src_=json.load(f)
        for s in src_:
            cur.execute(f"insert into {table}(Description ,   Details ,   Image ,   Title ,   Url ,   address ,   bathrooms ,   bedrooms ,   first_ts ,   furnished ,   id ,   latitude ,   longitude ,   petsallowed ,   posted ,   price ,   studio ,   ts) values(:Description ,   :Details ,   :Image ,   :Title ,   :Url ,   :address ,   :bathrooms ,   :bedrooms ,   :first_ts ,   :furnished ,   :id ,   :latitude ,   :longitude ,   :petsallowed ,   :posted ,   :price ,     :studio ,   :ts)",s)
    
    cur.execute(f"select count(*) from {table}")
    print(f"finished with: {cur.fetchone()[0]} ads")

def filter_and_insert(id,ad_dict,cur,table):
    bedrooms=re.compile(r'Beds\: (\d+) .*', re.IGNORECASE)
    studio=re.compile(r'studio|bachelor', re.IGNORECASE)
    j=ad_dict
    i=id
    # turn into a flat array
    j['id']=i

    # convert to iso
    if 'first_ts' not in j:
        # upgrading from old version
        j['first_ts'] = j['ts']

    if isinstance(j['ts'],float): # updated ts
        j['ts'] = date.fromtimestamp(j['ts']).isoformat()

    if isinstance(j['first_ts'],float): # new ad
        j['first_ts'] = date.fromtimestamp(j['first_ts']).isoformat()
        j['studio']=False
        # fix number of bedrooms if possible
    if 'studio' not in j:
        j['studio']=False

    if 'bedrooms' in j and isinstance(j['bedrooms'], str): # convert old entry?
        if 'bedrooms' in j and j['bedrooms']!='':
            j['bedrooms']=int(j['bedrooms'])
        else:
            j['bedrooms']=0

        if j['bedrooms'] == 0:
            # try to get from Details
            match=bedrooms.match(j["Details"])
            if match:
                j['bedrooms']=int(match.group(1))
                j['studio']=False
            elif studio.match(j["Details"]): 
                j['bedrooms']=0
                j['studio']=True
            # TODO: try to parse Title otherwise
        # fix bathrooms, assume that there is at leas one
        if j['bathrooms']=="" or j['bathrooms']=="10":
            j['bathrooms']=1
        else:
            j['bathrooms']==int(j['bathrooms'])/10  # don't know why it is 20 instead of 2

        if 'area' in j:
            try:
                j['area']=float(j['area'])
            except:
                j['area']=0

        if 'petsallowed' in j:
            try:
                j['petsallowed']=int(j['petsallowed'])
            except:
                j['petsallowed']=0
            
        if 'furnished' in j :
            try:
                j['furnished']=int(j['furnished'])
            except:
                j['furnished']=0
    #print(repr(j))
    # insert into db
    cur.execute(f"insert into {table}(Description ,   Details ,   Image ,   Title ,   Url ,   address ,   bathrooms ,   bedrooms ,   first_ts ,   furnished ,   id ,   latitude ,   longitude ,   petsallowed ,   posted ,   price ,   studio ,   ts) values(:Description ,   :Details ,   :Image ,   :Title ,   :Url ,   :address ,   :bathrooms ,   :bedrooms ,   :first_ts ,   :furnished ,   :id ,   :latitude ,   :longitude ,   :petsallowed ,   :posted ,   :price ,     :studio ,   :ts)",j)

def main(): # Main function, handles command line arguments and calls other functions for parsing ads
    options=parse_options()
    if options.url is None and options.import_json is None:
        print('Run with --help')
    else:
        url_to_scrape = options.url
        
        if options.exclude is not None:
            exclude_list = list() # TODO: finish
        else:
            exclude_list = list()
    
    conn = sqlite3.connect(options.db)
    print(f"Using {options.table} table in {options.db} db")

    conn.execute(f"create table if not exists {options.table}(Description text,   Details text,   Image text,   Title text,   Url text,   address text,   bathrooms numeric,   bedrooms numeric, first_ts text,   furnished integer,   id integer,   latitude numeric,   longitude numeric,   petsallowed integer,   posted text,   price numeric,   rentby text,   studio integer,   ts text)")
    conn.execute(f"create index if not exists {options.table}_id on {options.table}(id)")
    # convert to a dictionary
    #old_ad_dict = {i['id']:i for i in old_ads }
    if options.import_json is not None:
        import_json(options.import_json, conn, options.table)
    else:
        scrape(url_to_scrape, exclude_list, conn, options.table)

    # make a backup?
    # with open(options.output,'w') as f:
    #     json.dump(new_ads,f,indent=2,sort_keys=True)
    conn.commit()

if __name__ == "__main__":
    main()
