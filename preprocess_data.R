# script to load data from database
# and setup packages needed for data processing
rm(list=ls())

library(tidyverse)
library(jsonlite)
library(sf)
library(geojsonsf)
library(osmdata)
#

# cache montreal bounding box
if(file.exists("montreal_bb.RDS")) {
  mtl_bb <-readRDS(file="montreal_bb.RDS")
} else {
  mtl_bb <- getbb('Montreal', format_out='sf_polygon')
  saveRDS(mtl_bb, file = "montreal_bb.RDS")
}


# Saint-Helen Island
if(file.exists("mtl_land.RDS")) {
  mtl_land<-readRDS(file="mtl_land.RDS")
} else {
  mtl_land<-(opq(bbox='Montreal, Canada')%>%
    add_osm_feature(key = 'name:en', value = "Island of Montreal") %>% 
    osmdata_sf())$osm_multipolygons%>%st_transform(32188)
  saveRDS(mtl_land, file = "mtl_land.RDS")
}



# cache Longueuil bounding box
if(file.exists("longueuil_bb.RDS")) {
  longueuil <-readRDS(file="longueuil_bb.RDS")
} else {
  longueuil <- getbb('Longueuil', format_out='sf_polygon')
  saveRDS(longueuil, file = "longueuil_bb.RDS")
}

# cache st. Lambert bounding box
if(file.exists("st_lambert_bb.RDS")) {
  st_lambert <-readRDS(file="st_lambert_bb.RDS")
} else {
  st_lambert <- getbb('Saint-Lambert,QC', format_out='sf_polygon')
  saveRDS(longueuil, file = "st_lambert_bb.RDS")
}

# cache STM subway lines
if(file.exists("subway_p.RDS")){
  subway_p<-readRDS(file="subway_p.RDS")
} else {
# take only subways 
  stm<-st_read('stm/stm_lignes_sig.shp')
  subway<-stm%>%filter(route_id<10)
  subway_p<-st_transform(subway,32188)
  saveRDS(subway_p, file = "subway_p.RDS")
}

# STM stops
if(file.exists("stm_stop_p.RDS")){
  subway_stop_p<-readRDS(file="stm_stop_p.RDS")
} else {
# take only subway stops
  stm_stop<-st_read('stm/stm_arrets_sig.shp')
  stm_stop_p<-st_transform(stm_stop,32188)
  subway_stop_p<-stm_stop_p%>%filter(loc_type==2)
  saveRDS(subway_stop_p, file = "stm_stop_p.RDS")
}


# municipal data on property
if(file.exists("uniteevaluationfonciere.RDS")) {
  eval<-readRDS(file="uniteevaluationfonciere.RDS")
} else {
  # file from Montreal web site
  eval<-geojson_sf('uniteevaluationfonciere.geojson')
  eval<-st_transform(eval, 32188)
  saveRDS(eval, file = "uniteevaluationfonciere.RDS",compress='xz')
}

# Montreal neighborhoods
# load definition of neigbourhoods
mtl_p<-geojson_sf('quartierreferencehabitation.geojson') %>% 
  mutate(nom_arr=if_else(is.na(nom_arr),nom_mun,nom_arr)) %>% 
  mutate(nom_qr=if_else(is.na(nom_qr),nom_arr,nom_qr)) %>%
  st_transform(32188) %>% st_buffer(dist=0)

# aggregate across QR
mtl_pa<-mtl_p%>%group_by(nom_arr)%>%summarize() 

# the whole island borders
mtl_all<-mtl_p%>%summarize()%>%st_buffer(dist=0)%>%st_simplify(dTolerance=100)

if(file.exists("mtl_grid.RDS")) {
  mtl_grid<-readRDS(file="mtl_grid.RDS")
} else {
  # create hex mesh on top of Montreal 
  # 500m cell size
  mtl_grid<-st_make_grid(st_as_sfc(st_bbox(mtl_all)), cellsize = 500, square = FALSE)
  mtl_grid<-st_intersection(mtl_grid, mtl_all)
  # make an object with grid area and id
  mtl_grid<-st_sf(mtl_grid,area=st_area(mtl_grid),
    hexid=as.factor(seq(length(mtl_grid))),
    agr=c(area="aggregate",hexid="identity"))
  saveRDS(mtl_grid, file = "mtl_grid.RDS",compress='xz')
}

# and another , larger grid just for visualization
mtl_grid2<-st_make_grid(st_as_sfc(st_bbox(mtl_all)), cellsize = 2000, square = FALSE)
# remove anything outside of mtl
mtl_grid2<-st_intersection(mtl_grid2, mtl_all)
mtl_grid2<-st_sf(mtl_grid2,area=st_area(mtl_grid2),
                 hexid=as.factor(seq(length(mtl_grid2))),
                 agr=c(area="aggregate",hexid="identity"))

# all data is stored in sqlite database
con<-DBI::dbConnect(RSQLite::SQLite(), "property.sqlite3")

# read from db and remove some strange entries
kijiji_geo_p<-DBI::dbReadTable(con,"rental") %>% 
  filter(price>0, !is.na(price), price<5000,price>100) %>% 
  mutate(ts=as.Date(ts), first_ts=as.Date(first_ts), dur=ts-first_ts) %>% 
  st_as_sf(coords=c('longitude','latitude'),crs=4326) %>%
  st_intersection(mtl_bb) %>%
  st_transform(crs=32188)

# for survival analysis
kijiji_geo_p<-kijiji_geo_p%>%mutate(censored=(ts==max(kijiji_geo_p$ts)))

all_entries<-DBI::dbReadTable(con,"property") %>%
  filter(price>0) %>% 
  mutate(ts=as.Date(ts),photo_ts=as.Date(photo_ts),
         type=if_else(type=="Row / Townhouse",'House',type) ) # don't distinguish Townhouse from Houses

DBI::dbDisconnect(con)

# AirBNB data from InsideAirBNB
if(F) {
airbnb<-read_csv('airbnb_20191116_vis_listings.csv',
  col_types = cols(
  id = col_double(),
  name = col_character(),
  host_id = col_double(),
  host_name = col_character(),
  neighbourhood_group = col_logical(),
  neighbourhood = col_character(),
  latitude = col_double(),
  longitude = col_double(),
  room_type = col_character(),
  price = col_double(),
  minimum_nights = col_double(),
  number_of_reviews = col_double(),
  last_review = col_date(format = "%Y-%m-%d"),
  reviews_per_month = col_double(),
  calculated_host_listings_count = col_double(),
  availability_365 = col_double()
) ) %>% 
  st_as_sf(coords=c('longitude','latitude'),crs=4326) %>% 
  st_transform(crs=32188)
}

# set undefined data to NA
for(v in c('bathrooms', 'bedrooms', 'units', "area_interior", "area_exterior", "area_land",'stories','frontage') ) {
   all_entries[v][all_entries[v]==0]<-NA
}

# merge with data from the real estate agent
#sale<-read_csv('sale_prices_1.csv')
#all_entries<-all_entries %>% left_join(sale, by='mls')

# sort data, determine the first and the last day of the each listing and check if it is still on line
prop_final<-all_entries %>% 
  group_by(mls) %>% 
  dplyr::summarize(last_ts=max(ts), 
             first_ts=min(ts), 
             mprice=min(price),
             first_photo_ts=min(photo_ts, na.rm=T)) %>% 
  dplyr::rename(ts=last_ts)

# determine if still on market
first_date = min(prop_final$first_ts)
last_date  = max(prop_final$ts)

# active - existed at the last available date
# new - came to view after I started collecting statistics
prop_final <- prop_final %>% mutate( active=(ts==last_date), new=(first_ts>first_date) ) 

# should keep only the last entry for each mls ?
prop <- prop_final %>%
  inner_join(all_entries, by=c('mls','ts')) %>% 
  filter( bedrooms %in% c(1,2,3,4,5,6)) %>%
  mutate( bedrooms=as.factor(bedrooms), bathrooms=as.factor(bathrooms),units=as.factor(units),
    type=factor(type,levels=c("Apartment", "Duplex", "Triplex", "Fourplex", "House" )),
    date=as.numeric(ts),
    start_date=as.numeric(first_ts),
    time_on_market=as.numeric(if_else(!is.na(first_photo_ts) & ts>first_photo_ts, ts-first_photo_ts, ts-first_ts),
    mls=as.factor(mls))
  )

start_date_ <- min(prop$date)
end_date <- max(prop$date)

#### convert into sf object and project to local coordinate system
prop_geo_p<-prop %>% st_as_sf(coords=c('lng','lat'), crs=4326 ) %>% st_transform( crs=32188)

# merge with data from municipal DB
# fill out data  if it's available from muni DB
prop_geo_p<-st_join(prop_geo_p, eval, left=T,largest=T) %>%
  mutate(area_interior=if_else(is.na(area_interior), SUPERFICIE_BATIMENT*10.7639, area_interior),
         area_land=if_else(is.na(area_land), SUPERFICIE_TERRAIN*10.7639, area_land),
         year=ANNEE_CONSTRUCTION) %>% 
 mutate(price_sqft=price/area_interior)



# focus on some neighborhood
ROI_p<-mtl_p %>% filter( nom_arr %in% 
  c('Le Plateau-Mont-Royal',
    'Villeray–Saint-Michel–Parc-Extension',
    'Rosemont–La Petite-Patrie',
    "Verdun", 
    "Ahuntsic-Cartierville"), nom_qr!='Ile-des-Soeurs') %>% 
   mutate( arr=factor(nom_arr,levels=c('Le Plateau-Mont-Royal',
    'Villeray–Saint-Michel–Parc-Extension',
    'Rosemont–La Petite-Patrie',
    "Verdun", "Ahuntsic-Cartierville" ),labels=c('Plateau','Villeray','Rosemont','Verdun','Ahuntsic')),
     qr=as.factor(nom_qr))


# additional ROI that includes Longueul
longueuil_p<-st_transform(longueuil, 32188) %>% st_buffer(dist=0)
st_lambert_p<-st_transform(st_lambert, 32188) %>% st_buffer(dist=0)

# merge into mtl_p
longueuil_p$no_arr=0
longueuil_p$no_qr=0
longueuil_p$nom_arr='Longueul'
longueuil_p$nom_mun='Longueul'
longueuil_p$nom_qr='Longueul'

st_lambert_p$no_arr=0
st_lambert_p$no_qr=0
st_lambert_p$nom_arr='St. Lambert'
st_lambert_p$nom_mun='St. Lambert'
st_lambert_p$nom_qr='St. Lambert'

mtl_ext_p<-rbind(mtl_p,longueuil_p,st_lambert_p)

ROI_ext_p<-mtl_ext_p %>% filter( nom_arr %in% 
  c('Le Plateau-Mont-Royal',
    'Villeray–Saint-Michel–Parc-Extension',
    'Rosemont–La Petite-Patrie',
    "Verdun", 
    'Longueul',
    'St. Lambert',
    "Ahuntsic-Cartierville"), nom_qr!='Ile-des-Soeurs') %>% 
   mutate( arr=factor(nom_arr,levels=c('Le Plateau-Mont-Royal',
    'Villeray–Saint-Michel–Parc-Extension',
    'Rosemont–La Petite-Patrie',
    "Verdun", 'Longueul','St. Lambert', "Ahuntsic-Cartierville" ),
     labels=c('Plateau','Villeray','Rosemont','Verdun','Longueul','St. Lambert','Ahuntsic')),
     qr=as.factor(nom_qr))

# filter kijiji
kijiji_geo_p<-kijiji_geo_p %>% st_join(mtl_ext_p, left=T, largest=T)

# remove outliers (below 1% or above 99%)
kijiji_price_limits<-kijiji_geo_p%>%as.data.frame()%>%group_by(bedrooms, nom_qr)%>%
  summarize(price_low = quantile(price,0.01), price_high = quantile(price,0.99))
  
kijiji_geo_p<-kijiji_geo_p %>% left_join(kijiji_price_limits,by=c('bedrooms','nom_qr')) %>% 
  filter(price<=price_high,price>=price_low) %>% dplyr::select(-price_high,-price_low)

# merge with neighborhood information 
prop_geo_p<-st_join(prop_geo_p, mtl_ext_p, left=F)

rm(list=c('prop','prop_final','all_entries','con'))

# second cup cafe: 45.515579, -73.575935
ref_home<-data.frame(latitude=45.515989, 
                longitude=-73.575249,
                bedrooms=factor(2,levels=c(1,2,3,4,5,6)), 
                parking=factor(T,levels=c(F,T)), 
                bathrooms=factor(1,levels=levels(prop_geo_p$bathrooms)),
                stories=3,
                area_interior=784)%>%
  st_as_sf(coords=c('longitude','latitude'),crs=4326) %>% 
  st_transform(crs=32188, check=T, partial=F)  

# 6666 St. Urban
ref_work<-data.frame(latitude=45.530657, 
                longitude=-73.613654)%>%
  st_as_sf(coords=c('longitude','latitude'),crs=4326) %>% 
  st_transform(crs=32188, check=T, partial=F)  


save(list=ls(),file='preprocessed.RData',compress='xz')
