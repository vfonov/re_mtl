#! /bin/bash

# a crawler that is run everyday to update information

# setup environment
# conda activate <your conda environment>

# setup parameters

IN= # < where to keep a backup of data from centris>
OUT= # < where to keep final sqlite database>
PREFIX= # <scripts location>

# scrape realtor, dump data in .json.gz format
python $PREFIX/scrapper.py $IN

# scrape kijiji for Montreal
python $PREFIX/kijiji_scraper.py 'https://www.kijiji.ca/b-appartement-condo/ville-de-montreal/c37l1700281?ad=offering' --db $OUT/property.sqlite3
# scrape for south shore
python $PREFIX/kijiji_scraper.py 'https://www.kijiji.ca/b-appartement-condo/longueuil-rive-sud/c37l1700279?ad=offering' --db $OUT/property.sqlite3

# summmarize from realtor inside sqlite3 database
python $PREFIX/summarize.py $IN $OUT/property.sqlite3

# preprocess data for further statistical analysis
cd $PREFIX
Rscript preprocess_data.R


# regenerate website - this will update files in docs

Rscript -e "rmarkdown::render_site('index.Rmd')"
Rscript -e "rmarkdown::render_site('stats_habr.Rmd')"
