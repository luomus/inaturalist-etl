# iNaturalist to FinBIF ETL Process

This repository contains a set of Python scripts designed to facilitate an ETL (Extract-Transform-Load) process for synchronizing biodiversity occurrence records from iNaturalist to the Finnish Biodiversity Information Facility (FinBIF) data warehouse. The scripts retrieve data from the iNaturalist open REST API, transform it into the FinBIF-compatible format, and then submit the processed records to the FinBIF REST API. Once submitted, the data is made available on the FinBIF portal at Laji.fi. Additionally, the data is stored in a private data warehouse for restricted access by Finnish public authorities, enriched with private location coordinates from iNaturalist's annual data exports.

The scripts are containerized using Docker and can be executed either manually via the command line or automatically using a cron-based scheduler. The process tracks the last synchronization timestamp and ensures that only records updated or created after that time are synced. It also supports partial synchronization, allowing users to focus on specific subsets of data, such as captive/cultivated observations or obscured records. Currently, deletions are not handled, as iNaturalist's API does not provide deletion information.

## Setup

* git clone https://github.com/luomus/inaturalist-etl.git
* mkdir app/privatedata
    * Add private data files here, see below
* cp .env.example .env
    * Add your Laji.fi API tokens to this file.
* cp app/store/data.example.json app/store/data.json
* docker-compose up; docker-compose down;

## Running

To run scripts manually, start with:

    docker exec -ti inat_etl bash
    cd app

### Debug single observation

    python3 single.py 194920696 dry 

### Update all

Get **all** observations updated since last run and post them to DW. Replace `staging` with `production` in order to push into production. This depends on variables in `store/data.json`. The number is sleep time in seconds between page requests, to avoid overloading the iNat API.

    python3 inat.py staging auto 10

This script runs until it has reached end of observations, or until it fails due to an error. It should be called automatically to set up fully automatic ETL process.

### Update filtered observations

Get **specified** observations updated since last run, and post to DW. This also depends on variables in `store/data.json`, including urlSuffix, which can be used to filter observations from iNaturalist API.

    python3 inat.py staging manual

Example suffixes:

* `&` # for no filtering
* `&captive=true`
* `&quality_grade=casual`
* `&user_id=username`
* `&project_id=105081`
* `&photo_licensed=true`
* `&taxon_name=Parus%20major` # only this taxon, not children, use %20 for spaces
* `&taxon_id=211194` # Tracheophyta; this taxon and children
* `&user_id=mikkohei13&geoprivacy=obscured%2Cobscured_private%2Cprivate` # test with obscured  observations
* `&place_id=165234` # Finland EEZ
* `&term_id=17&term_value_id=19` # with annotation attribute dead (not necessarily upvoted?)
* `&term_id=12` # with an annotation for Flowers and Fruit
* `&field:Host` # Observation field regardless of value
* `&field:Host%20plant`
* `&field:Isäntälaji`
* `&field:Lintuatlas,%20pesimävarmuusindeksi`
* `&rank=subspecies`
* `&d1=2018-01-01&d2=2020-12-31` # observation dates

Use iNaturalist API documentation to see what kind of parameters you can give: https://api.inaturalist.org/v1/docs/#!/Observations/get_observations


### How it works

* inat.py
    * Get startup variables from `store/data.json`
    * Loads private data to Pandas dataframe
    * Gets data from iNat and goes through it page-by-page. Uses custom pagination, since iNat pagination does not work past 333 (?) pages.
* inatToDW.py
    * Converts all observations to DW format
    * Adds private data if it's available, to a privateDocument
* postDW.py
    * Posts all observations to FinBIF DW as a batch
* inat.py
    * If success, sets vatiables to `store/data.json`


## Preparing private data

* Download private data from https://inaturalist.laji.fi/sites/20
* Unzip the data
* Copy `inaturalist-suomi-20-observations.csv` file to `/app/privatedata/`
* Run script `app/tools/simplify.py` for this file
* Delete the `inaturalist-suomi-20-observations.csv` file
* Copy `inaturalist-suomi-20-users.csv` file to `/app/privatedata/`
* Double-check that Git doesn't see the files, by running `git status`
* Test with Mikko's observations by running manual script with filters:
    * `inat_MANUAL_urlSuffix = &user_id=mikkohei13&geoprivacy=obscured%2Cobscured_private%2Cprivate`
    * `inat_MANUAL_production_latest_obsId = 0`
    * `inat_MANUAL_production_latest_update = 2023-01-01T00%3A25%3A15%2B00%3A00`
* Update all data by running inat_manual with filters:
   * `inat_MANUAL_production_latest_obsId = 0`
   * `inat_MANUAL_production_latest_update = 2000-01-01T00%3A25%3A15%2B00%3A00`
   * `inat_MANUAL_urlSuffix = &geoprivacy=obscured%2Cobscured_private%2Cprivate`
* Note that this updates only those observations that are **currently** obscured. Updating all observations with email addresses would require updating all observations, which would take day(s).


## FAQ: Why observation on iNat is not visible on Laji.fi?

- Laji.fi hides non-wild observations by default.
- Laji.fi hides observations that have issues, or have been annotated as erroneous.
- Laji.fi obscures certain sensitive species, which then cannot be found using all filters, e.g. date filter.
- Taxonomy issues. ETL process and annotations can change e.g. taxon, so that the observation cannot be found with the original name.
- If observation has first been private or captive, and then changed to public or non-captive, it may not be copied by the regular copy process.

## Todo

### Issues:

- Deletions.
- If location of an observation is first set to Finland, then copied to DW, then location is changed on iNaturalist to some other country, changes won't come to DW, since he system only fetches Finnish observations.
    - Solution: Twice per year, check all occurrences against Finnish data dump. If observation is not found, it's deleted or moved outside Finland -> Delete from DW: Check: data dump should contain all Finnish observations, regardless of user affiliation.
    - Problem: the data dump does not contain observations submitted after the data dump has been created.
- Spaces in date variables will cause fatal error with iNat API -> should strip the string

### Should/Nice to have:

- Monitor consistent failures on Rahti by Zabbix
- Fix date created timezone
- Monitor if iNat API changes (test observation)
- Conversion: annotation key 17 (Alive or dead) once the valua can be handled by FinBIF DW ETL, the verify it works
   - https://laji.fi/observation/list?collectionId=HR.3211&alive=false
- Conversion: Remove spaces, special chars etc. from fact names, esp. when handling observation fields
- Conversion: See todo's from conversion script
