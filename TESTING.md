# Testing Guide

The container runs, executes the ETL process, and exits.

```bash
docker build -t inat-etl .
docker run --rm --env-file .env inat-etl
```

This will:
1. Download data from Allas
2. Run default command `python inat.py production auto true 5`
3. Exit when finished

### Run inat.py with custom parameters

Override the default CMD to pass your own arguments:

```bash
docker run --rm --env-file .env inat-etl staging manual true 10
```

Arguments are: `<target> <mode> <full_logging> [sleep]`
- `target`: `staging` or `production`
- `mode`: `auto` or `manual`
- `full_logging`: `true` or `false`
- `sleep`: optional, seconds between requests (default 10)

### Run single.py for debugging

To run `single.py` for testing individual observations:

```bash
docker run --rm --env-file .env inat-etl single.py 194920696 dry
```

The entrypoint will detect that the first argument is a script name (ends with `.py`) and run that script instead of `inat.py`.

## Notes

- `--rm` flag removes the container after it exits (keeps things clean)
- The container always downloads data from Allas first (even for single.py runs)
- All code is baked into the image - no volume mounts needed
- For live code editing during development, you can temporarily add a volume mount in docker-compose.yml
