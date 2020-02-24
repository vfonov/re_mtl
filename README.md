# Spatiotemporal statistics of Montreal Real Estate

## Scripts
- `scrapper.py` - scrapper from MLS system, dowload data about Montreal and the South Shore, stored information in gzipped json files
- `kijiji_scraper.py` - generic kijiji scrapper, stored information in `property.sqlite3` database
- `summarize.py` - processed data from MLS system, from gzipped json file(s) and stores it in `property.sqlite3`
- `preprocess_data.R` - R script , performing some basic preoprocessing and filtering data from `property.sqlite3` outputs `preprocessed.RData`
- `environment.yml` - conda environment description
- `run_scrapper.sh` - template of a shell script tying it all together
- `index.Rmd` - knitr script, used to generate http://www.ilmarin.info/re_mtl
- `stats_habr.Rmd` - knitr script , used to generate http://www.ilmarin.info/re_mtl/stats_habr.html

## Data files
these files can be downloaded from https://github.com/vfonov/re_mtl/releases/tag/v0.0 
- `uniteevaluationfonciere.geojson.xz` - downloaded from http://donnees.ville.montreal.qc.ca/dataset/unites-evaluation-fonciere/resource/866a3dbc-8b59-48ff-866d-f2f9d3bbee9d
- `property.sqlite3.xz` - archive of the raw property data
- `preprocessed.RData` - preprocessed data, generated from `property.sqlite3` by `preprocess_data.R` script

## Requirements
- R version 3.6

## Installing
```
conda env create --name re_mtl -f environment.yml

# to download preprocessed data
curl -L https://github.com/vfonov/re_mtl/releases/download/v0.0/preprocessed.RData -o preprocessed.RData

# to download raw data
curl -L https://github.com/vfonov/re_mtl/releases/download/v0.0/property.sqlite3.xz -o property.sqlite3.xz
unxz property.sqlite3.xz 

```

## Running
```
conda activate re_mtl

# to regenerate preprocessed.RData
Rscript preprocess_data.R

# to regenerate contents of http://www.ilmarin.info/re_mtl/
Rscript -e "rmarkdown::render_site('index.Rmd')" 
```
