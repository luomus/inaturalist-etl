# iNaturalist to FinBIF ETL Process

This repository contains a set of Python scripts designed to facilitate an ETL (Extract-Transform-Load) process for synchronizing biodiversity occurrence records from iNaturalist to the Finnish Biodiversity Information Facility (FinBIF) data warehouse. The scripts retrieve data from the iNaturalist open REST API, transform it into the FinBIF-compatible format, and then submit the processed records to the FinBIF REST API. Once submitted, the data is made available on the FinBIF portal at Laji.fi. Additionally, the data is stored in a private data warehouse for restricted access by Finnish public authorities, enriched with private location coordinates from iNaturalist's annual data exports.

The scripts are containerized using Docker and can be executed either manually via the command line or automatically using a cron-based scheduler. The process tracks the last synchronization timestamp and ensures that only records updated or created after that time are synced. It also supports partial synchronization, allowing users to focus on specific subsets of data, such as captive/cultivated observations or obscured records. Currently, deletions are not handled, as iNaturalist's API does not provide deletion information.

## Setup

* `git clone https://github.com/luomus/inaturalist-etl.git`
* `mkdir app/privatedata`
    * Add private data files here, see below
* `cp .env.example .env`
    * Add your Laji.fi API tokens to this file.
* `cp app/store/data.example.json app/store/data.json`

## Running in OpenShift

See [OPENSHIFT.md](OPENSHIFT.md) for running in OpenShift.

## Running in Docker container with data from Allas

First copy `data.json` and private data to Allas, using `-ALLAS` suffixes.

Then build and run the container, which will execute the ETL process, and exit:

```bash
docker build -t inat-etl .
docker run --rm --env-file .env inat-etl
```

This will:
1. Download data from Allas
2. Run default command `python inat.py production auto true 5`
3. Exit when finished

### Run with custom parameters

Override the default CMD to pass your own arguments.

```bash
docker build -t inat-etl .
docker run --rm --env-file .env inat-etl production manual true 5
```

Arguments are: `<target> <mode> <full_logging> [sleep]`
1. `target`: `staging` or `production`
2. `mode`: `auto` or `manual`
3. `full_logging`: `true` or `false`
4. `sleep`: optional, seconds between requests (default 10)

Manual update will use private data from Allas but local parameters from `store/data-MANUAL.json`. Use this file to set the parameters for the update. **Note: you need to build the container again if you change the parameters!**

Example suffixes below. Use iNaturalist API documentation to see what kind of parameters you can give: https://api.inaturalist.org/v1/docs/#!/Observations/get_observations

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
* `&field:Habitat`
* `&field:Lintuatlas,%20pesimävarmuusindeksi`
* `&rank=subspecies`
* `&d1=2018-01-01&d2=2020-12-31` # observation dates

### Run single.py for debugging

To run `single.py` for testing individual observations:

```bash
docker run --rm --env-file .env inat-etl single.py 194920696 dry
```
The entrypoint will detect that the first argument is a script name (ends with `.py`) and run that script instead of `inat.py`.

Arguments are: `<script> <observation_id> <target> <mode>`
1. `script`: `single.py`
2. `observation_id`: ID of the observation to test
3. `target`: `staging` or `production`
4. `mode`: `dry` or `dry-verbose`

### Notes

- `--rm` flag removes the container after it exits (keeps things clean)
- The container always downloads data from Allas first (even for single.py runs)
- All code is baked into the image - no volume mounts needed
- For live code editing during development, you can temporarily add a volume mount in docker-compose.yml

## How the system works

* inat.py
    * Get startup variables from `store/data.json`
    * Loads private data to Pandas dataframe
* getInat.py
    * Gets data from iNat and goes through it page-by-page. Uses custom pagination, since iNat pagination does not work past 333 pages.
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

- Deletions, which cannot be done using data from public API.
- If location of an observation is first set to Finland, then copied to DW, then location is changed on iNaturalist to some other country, changes won't come to DW, since he system only fetches Finnish observations.
    - Solution: Twice per year, check all occurrences against Finnish data dump. If observation is not found, it's deleted or moved outside Finland -> Delete from DW.
    - Problem: the data dump does not contain observations submitted after the data dump has been created.

### Should/Nice to have:

- Fix date created timezone
- Monitor if iNat API changes (test observation)
- Conversion: annotation key 17 (Alive or dead) once the valua can be handled by FinBIF DW ETL, the verify it works
   - https://laji.fi/observation/list?collectionId=HR.3211&alive=false
- Conversion: Remove spaces, special chars etc. from fact names, esp. when handling observation fields
- Conversion: See todo's from conversion script
