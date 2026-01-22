
import sys
import pprint

import getInat
import inatToDw
import postDw

import json
import pandas

import inatHelpers

"""
Test observations
puolukkapiiloyökkönen 60063865 - tags, obs fields, desc with html, annotations
TODO, 3 photos and 1 sound, annotations, traditional projects, tag, observation fields, copyrighted media
(joku)hopeatäplä 53608382 - coll and trad projects, annotations (also negative)
ohdakeperhonen 39330050 - locality names
TODO, 9 photos
mittari 60201865 - karkeistettu -> box coordinates
sieni lehdellä 60934016 - yksityinen -> ei koordinaatteja
sammal 62132113 - ei koordinaattien tarkkuutta
tolppa 55900883 - quality metrics
kissa 60213784 - quality metrics given by user who no longer exist (probably?)

Flagged observations to test with:
https://www.inaturalist.org/flags?commit=Suodata&flaggable_type=Observation&flagger_name=&flagger_type=any&flagger_user_id=&flags%5B%5D=other&page=3&reason_query=&resolved=no&resolver_name=&resolver_user_id=&user_id=&user_name=&utf8=%E2%9C%93

"""

# Input
# TODO: Input validation?
id = sys.argv[1] # id of the iNat observation
target = sys.argv[2] # dry | dry-verbose | production

# Load private data
privateObservationData = pandas.read_csv("./privatedata/latest-ALLAS.tsv", sep='\t')

# Exclude the last row if it is empty
# Check if the last row is indeed empty
if privateObservationData.iloc[-1].isnull().all():
  privateObservationData = privateObservationData.iloc[:-1]

private_emails = inatHelpers.load_private_emails()

# Get and transform data
singleObservationDict = getInat.getSingle(id)

dwObservation, lastUpdateKey = inatToDw.convertObservations(singleObservationDict['results'], privateObservationData, private_emails)

#print("TEMP DEBUG lastUpdateKey: " + str(lastUpdateKey))


# Output
pp = pprint.PrettyPrinter(indent=2)

if "staging" == target or "production" == target:
  postDw.postSingle(dwObservation, target)

if "dry-verbose" == target:
  print("INAT:")
  print(singleObservationDict['results'])

if "dry-verbose" == target or "dry" == target:
  print("--------------------------------------------------------------")
  print("pp.pprint(dwObservation):")
  pp.pprint(dwObservation)

  print("--------------------------------------------------------------")
  print("json.dumps(dwObservation):")
  print(json.dumps(dwObservation))

