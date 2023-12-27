
#from collections import defaultdict
import json # for debug
import copy

import inatHelpers

"""
BUGFIXES COMPARED TO PHP-VERSION 9/2020:
- If quality was less than -1, not marked as unreliable. Must reprocess all.
- If obs had multiple ARR images, multiple image_arr keywords were set.
- Obscured obs coordinate box was calculated incorrectly
- Obscured obs accuracy was set to 0
- Annotations were saved incorrectly, so that also negative and tied votes resulted in positive annotation and fact.
- If observation was private, it was skipped ("Skipped observation not from Finland"), because private observation have no place_id's. 

NOTES/CHANGES COMPARED TO PHP-VERSION 9/2020:
- Script expects that all observations are from Finland, so it fills in hardcoded country name. Must change this if also foreign observations ar handled.
- DW removes/hides humans, so handling them here is not needed. (Used to make them private, remove images and description.)
- What to do if observation contains 1...n copyright infringement flagged media files? E.g. https://www.inaturalist.org/observations/46356508
- Earlier removed FI, Finland & Suomi from the location name, but not anymore
- Previously used copyright string, now just user name for photo attribution, since license in separate field.
- Unit fact taxonByUser changed name to species_guess, which is the term used by iNat. Logic of this field in iNat is unclear.
- observerActivityCount is not used, since it increases over time -> is affected by *when* the observation was fetched from iNat.
- Note that at least annotations and quality metrics appear on the iNat API after a delay (c. 15 mins cache?)

DW data features:
- There can be multiple facts with the same name
- Keywords have to be strings (int will cause a failure)
- Fields can be left blank
- Enum values are ALL-CAPS

Note:
- If an observation moified that it become private, the private coordinates will go to private DW only after next data dump form iNaturalist, since public observations are removed from the private data file (to speed up the system)

"""


def skipObservation(inat):
  # Note: This is only for skipping observations that don't YET have enough info to be worthwhile to be included to DW. Don't skip e.g. spam here, because then spammy observations would stay in DW forever. Instead mark them as having issues.

  if not inat["taxon"]:
    print(" skipping " + str(inat["id"]) + " without taxon.")
    return True
  elif not inat["observed_on_details"]:
    print(" skipping " + str(inat["id"]) + " without date.")
    return True
  else:
    return False


def appendKeyword(keywordList, inat, keywordName):
  # Handles only keys directly under root of inat

  if keywordName in inat: # Checks if key exists
    if inat[keywordName]: # Checks if value is truthy
      keywordList.append(keywordName)

  return keywordList


def appendCollectionProjects(factsList, keywords, projects):
  for nro, project in enumerate(projects):
    keywords.append("project-" + str(project['project_id']))
    factsList.append({ "fact": "collectionProjectId", "value": project['project_id'] })
  return factsList, keywords


def appendTraditionalProjects(factsList, keywords, projects):
  for nro, project in enumerate(projects):
    keywords.append("project-" + str(project['project']['id']))
    factsList.append({ "fact": "traditionalProjectId", "value": project['project']['id'] })
  return factsList, keywords


def appendTags(keywordsList, tags):
  for nro, tag in enumerate(tags):
    keywordsList.append(tag)
  return keywordsList


def summarizeQualityMetrics(quality_metrics):
  summary = {}

  for nro, vote in enumerate(quality_metrics):
    # Skip vote if spam or suspended user, NOT TESTED
    if "user" in vote: # If user has been deleted, user is not set. Still handle the user's vote normally.
      # Skip spam and suspended user votes
      if vote["user"]["spam"]:
        continue
      if vote["user"]["suspended"]:
        continue 

    # Calculate vote
    if True == vote["agree"]:
      value = 1
    elif False == vote["agree"]:
      value = -1
    else:
      value = 0 

    # Init if not set
    if vote["metric"] not in summary:
      summary[vote["metric"]] = 0 

    summary[vote["metric"]] = summary[vote["metric"]] + value

  return summary


def getLicenseUrl(licenseCode):
  licenses = {}
  licenses["cc0"] = "http://tun.fi/MZ.intellectualRightsCC0-4.0"
  licenses["cc-by"] = "http://tun.fi/MZ.intellectualRightsCC-BY-4.0"
  licenses["cc-by-nc"] = "http://tun.fi/MZ.intellectualRightsCC-BY-NC-4.0"
  licenses["cc-by-nd"] = "http://tun.fi/MZ.intellectualRightsCC-BY-ND-4.0"
  licenses["cc-by-sa"] = "http://tun.fi/MZ.intellectualRightsCC-BY-SA-4.0"
  licenses["cc-by-nc-nd"] = "http://tun.fi/MZ.intellectualRightsCC-BY-NC-ND-4.0"
  licenses["cc-by-nc-sa"] = "http://tun.fi/MZ.intellectualRightsCC-BY-NC-SA-4.0"

  if not licenseCode:
    return "http://tun.fi/MZ.intellectualRightsARR"
  else:
    if licenseCode in licenses:
      return licenses[licenseCode]
    else:
      print("Unknown license code " + str(licenseCode))
      return "http://tun.fi/MZ.intellectualRightsARR"


def getImageData(photo, observer):
  squareUrl = photo['photo']['url']

  thumbnailUrl = inatHelpers.getProxyUrl(squareUrl, "small")
  fullUrl = inatHelpers.getProxyUrl(squareUrl, "original")

  photoDict = {}
  photoDict['thumbnailURL'] = thumbnailUrl
  photoDict['fullURL'] = fullUrl
  photoDict['copyrightOwner'] = observer
  photoDict['author'] = observer
  photoDict['licenseId'] = getLicenseUrl(photo['photo']['license_code'])
  photoDict['mediaType'] = "IMAGE"
  return photoDict


# Check if is NaN value
def hasValue(val):
  if val == val:
    return True
  else:
    return False


def convertObservations(inatObservations, privateObservationData, private_emails):
  """Convert observations from iNat to FinBIF DW format.

  Args:
  inat (orderedDictionary): single observation in iNat format.

  Raises:
  Exception: 

  Returns:
  orderedDictionary: multiple observations in FinBIF DW format
  False: if observation should not be posted to DW

  Test:
  - obs without observed_on_details
  """


  dwObservations = []
  lastUpdateKey = 0

  # For each observation
  for nro, inat in enumerate(inatObservations):

    # Get private data
    privateData = privateObservationData.loc[privateObservationData['id'] == inat["id"]]
    privateData = privateData.to_dict(orient='records')

    logSuffix = ""

    has_private_data = False
    if privateData:
      has_private_data = True
      logSuffix = logSuffix + " has private data"
      privateData = privateData[0]

    # Get private emails
    has_private_email = False
    if inat['user']['login'] in private_emails:
      has_private_email = True
      private_email = private_emails[inat['user']['login']]
      logSuffix = logSuffix + " has private email"


    print("Converting obs " + str(inat["id"]), end = logSuffix)

#    exit()
    
    # Debug
#    jsonData = json.dumps(inat)
#    print(jsonData)
#    exit()

    # Skip incomplete observations
    if skipObservation(inat):
      continue

#    dw = defaultdict(dict)

    # Prepare elements of the observation
    dw = {}
    publicDocument = {}
    gathering = {}
    unit = {}

    desc = {}

    keywords = []
    documentFacts = []
    gatheringFacts = []
    unitFacts = []
    
    # Init empty values
    gathering['notes'] = ""
    unit['sourceTags'] = []
    unit["quality"] = {}
    unit["quality"]["issue"] = {}

    # -------------------------------------
    # Conversions

    # Data shared by all observations
    collectionId = "http://tun.fi/HR.3211"

    dw["collectionId"] = collectionId
    publicDocument['collectionId'] = collectionId

    dw['sourceId'] = "http://tun.fi/KE.901"
    dw['schema'] = "laji-etl"
    publicDocument['secureLevel'] = "NONE"
    publicDocument['concealment'] = "PUBLIC"


    # Add secure reasons
    # null or "open" means that observation is not private 
    publicDocument['secureReasons'] = []
    if not ("open" == inat["taxon_geoprivacy"] or None == inat["taxon_geoprivacy"]):
      publicDocument['secureReasons'].append("DEFAULT_TAXON_CONSERVATION")
    if not ("open" == inat["geoprivacy"] or None == inat["geoprivacy"]):
      publicDocument['secureReasons'].append("USER_HIDDEN_LOCATION")


    # Identifiers
    documentId = dw["collectionId"] + "/" + str(inat["id"])
    dw["documentId"] = documentId
    publicDocument['documentId'] = documentId
    gathering['gatheringId'] = documentId + "-G"
    unit['unitId'] = documentId + "-U"

    documentFacts.append({ "fact": "catalogueNumber", "value": inat['id']})
#    documentFacts.append({ "fact": "referenceURI", "value": inat['uri']}) # replaced with referenceURL
    keywords.append(str(inat['id'])) # id has to be string

    publicDocument['referenceURL'] = inat['uri'] # ADDITION

    # Taxon
    # Special handling for heracleums, to get giant hogweed records
    if "Heracleum" in inat['taxon']['name']:
      # loop identificatons. If any of them suggests any giant hogweed, and none suggests european hogweed, set as giant hogweed
      unit['taxonVerbatim'] = inatHelpers.convertTaxon(inat['taxon']['name'])

    else:
      # Scientific name iNat interprets this to be, special cases converted to match FinBIF taxonomy
      unit['taxonVerbatim'] = inatHelpers.convertTaxon(inat['taxon']['name'])

      # Name observer or identifiers(?) have given, can be any language
      unitFacts.append({ "fact": "species_guess", "value": inat['species_guess']})

      # Scientific name iNat interprets this to be
      unitFacts.append({ "fact": "taxonInterpretationByiNaturalist", "value": inat['taxon']['name']})


    # Observer
    # Observer name, prefer full name over loginname
    if inat['user']['name']:
      observer = inat['user']['name']
    else:
      observer = inat['user']['login']

    gathering['team'] = []
    gathering['team'].append(observer)


    # Editor & observer id
    userId = "inaturalist:"  + str(inat['user']['id'])
    publicDocument['editorUserIds'] = []
    publicDocument['editorUserIds'].append(userId)
    gathering['observerUserIds'] = []
    gathering['observerUserIds'].append(userId)


    # Orcid
    if inat['user']['orcid']:
      documentFacts.append({ "fact": "observerOrcid", "value": inat['user']['orcid']}) 


    # Description
    if inat["description"]:
      gathering['notes'] = gathering['notes'] + inat["description"]


    # Wildness
    if 1 == inat["captive"]:
      unit['wild'] = False


    # Projects
    # Non-traditional / Collection (automatic)
    if "non_traditional_projects" in inat:
      documentFacts, keywords = appendCollectionProjects(documentFacts, keywords, inat['non_traditional_projects'])
    
    # Traditional (manual)
    if "project_observations" in inat:
      documentFacts, keywords = appendTraditionalProjects(documentFacts, keywords, inat['project_observations'])


    # Dates
    publicDocument['createdDate'] = inat['created_at_details']['date']

    updatedDatePieces = inat['updated_at'].split("T")
    publicDocument['modifiedDate'] = updatedDatePieces[0]

    gathering['eventDate'] = {}
    gathering['eventDate']['begin'] = inat['observed_on_details']['date']
    gathering['eventDate']['end'] = gathering['eventDate']['begin'] # End always same as beginning

    documentFacts.append({ "fact": "observedOrCreatedAt", "value": inat['time_observed_at']}) # This is the exact datetime when observation was saved


    # Locality
    # Locality name used to be reversed, but not needed really?
    gathering['locality'] = inat['place_guess']
    gathering['country'] = "" # Finland removed as country, so that fixing observations outside Finland is possible. iNaturalist does not have dedicated country field, country name is sometimes included on the place_guess field.


    # Tags
    if "tags" in inat:
      keywords = appendTags(keywords, inat["tags"])

    
    # Photos
    photoCount = len(inat['observation_photos'])
    if photoCount >= 1:
      unit['media'] = []
      keywords.append("has_images") # Needed for combined photo & image search
      unitFacts.append({ "fact": "imageCount", "value": photoCount})
      unit['externalMediaCount'] = photoCount # ADDITION

      arrImagesIncluded = False

      if photoCount > 4:
        keywords.append("over_4_photos")

      for nro, photo in enumerate(inat['observation_photos']):
        # Facts
        photoId = str(photo['photo']['id'])
        unitFacts.append({ "fact": "imageId", "value": photoId})
        unitFacts.append({ "fact": "imageUrl", "value": "https://www.inaturalist.org/photos/" + photoId})

        # Photo
        '''
        What should be changed if we want to show arr-images on PAP?
        - handle all photos here; no if/else
        - at the end of this file, remove images without a license from th public document, and add keyword [keywords.append("image_arr")]
        '''
        # If photo has a CC-license
        if photo['photo']['license_code']:
          unit['media'].append(getImageData(photo, observer))
        # If photo does not have a license, it's "all rights reserved" -> don't handle images
        else:
          arrImagesIncluded = True 

      if arrImagesIncluded:
        keywords.append("image_arr") # Set if at least one photo is missing license   


    # Sounds
    soundCount = len(inat['sounds'])
    # Note: if audio is later linked via proxy, need to check that cc-license is given 
    if soundCount >= 1:
      keywords.append("has_audio") # Needed for combined photo & image search
      unitFacts.append({ "fact": "soundCount", "value": soundCount})

      if soundCount > 1:
        keywords.append("over_1_sounds")

      for nro, sound in enumerate(inat['sounds']):
        unitFacts.append({ "fact": "audioId", "value": sound['id']})
        unitFacts.append({ "fact": "audioUrl", "value": sound['file_url']})


    # Any media
    if 0 == soundCount and 0 == photoCount:
      keywords.append("no_media")


    # Observation fields
    hasSpecimen = False
    abundanceString = ""
    atlasCode = None

    for nro, val in enumerate(inat['ofvs']):
      unitFacts.append({ "fact": val['name_ci'], "value": val['value_ci']}) # This preserves zero values, which can be important in observation fields

      # Fields that are specifically supported by FinBIF
      if "Specimen" == val['name_ci']:
        hasSpecimen = True
      if "Yksilömäärä" == val['name_ci']:
        abundanceString = val['value_ci']
      if "Lintuatlas, pesimävarmuusindeksi" == val['name_ci']:
        atlasCode = inatHelpers.extractAtlasCode("atl:" + val['value_ci'])
      if "Host plant" == val['name_ci'] or "Host" == val['name_ci'] or "Isäntälaji" == val['name_ci'] or "Host" == val['name_ci']:
        if "taxon" in val:
          unitFacts.append({ "fact": "http://tun.fi/MY.hostInformalNameString", "value": val["taxon"]["name"]})

    unit['abundanceString'] = abundanceString

    # Maybe todo: Get atlascode only if is a bird (iconic_taxon_name == Aves)
    # If atlasCode not from observation field, try to get it from description
    if None == atlasCode:
      atlasCode = inatHelpers.extractAtlasCode(inat["description"])
    
    # Set atlasCode as a fact
    if None != atlasCode:
#      unitFacts.append({ "fact": "atlasCode", "value": atlasCode})
      unit['atlasCode'] = "http://tun.fi/MY.atlasCodeEnum" + atlasCode

    # Record basis
    if hasSpecimen:
      unit['recordBasis'] = "PRESERVED_SPECIMEN"
    elif photoCount >= 1:
      unit['recordBasis'] = "HUMAN_OBSERVATION_PHOTO"
    elif soundCount >= 1:
      unit['recordBasis'] = "HUMAN_OBSERVATION_RECORDED_AUDIO"
    else:
      unit['recordBasis'] = "HUMAN_OBSERVATION_UNSPECIFIED"


    # License URL's/URI's
    publicDocument['licenseId'] = getLicenseUrl(inat['license_code'])


    # Annotations
    if inat['annotations']:
      keywords.append("has_annotations")

      for nro, annotation in enumerate(inat['annotations']):
        key, value = inatHelpers.summarizeAnnotation(annotation)

        # Annotations voted against or tie, only keyword is saved
        if "keyword" == key:
          keywords.append(value)
        # Annotation voted for, added as unit fact
        else:
          # NOTE: If annotation is saved as keyword, make sure it's a string, not int.
          factName = "annotation_" + str(key)
          unitFacts.append({ "fact": factName, "value": str(value)})

        # Annotations with native values in DW:
        if "lifeStage" == key:
          unit['lifeStage'] = value
        elif "sex" == key:
          unit['sex'] = value
        elif "dead" == key:
          unit['dead'] = value # Todo: check that works

    # Quality metrics
    qualityMetricUnreliable = False
    if "quality_metrics" in inat:
      qualityMetricsSummary = summarizeQualityMetrics(inat["quality_metrics"])
#      exit(qualityMetricsSummary) # debug

      for metric, value in qualityMetricsSummary.items():
        # Add to facts
        metricName = "quality_metrics_" + metric
        unitFacts.append({ "fact": metricName, "value": str(value)})

        # If at least one negative quality metric, mark as unreliable. Exception: non-wilds are handled elsewhere.
        if "wild" != metric:
          if value < 0:
            qualityMetricUnreliable = True


    # Quality on DW

    # Negative quality metrics (thumbs down) 
    # This will make observation uncertain in dw, bot no issue
    if qualityMetricUnreliable:
      unit['sourceTags'].append("EXPERT_TAG_UNCERTAIN")
      keywords.append("quality-metric-unreliable")


    # Flags
    # TODO: Has not been tested!
    if inat["flags"]:
      unit['sourceTags'].append("EXPERT_TAG_UNCERTAIN")
      keywords.append("flagged")
      gathering['notes'] = gathering['notes'] + "\n\[Observation flagged on iNaturalist as problematic or duplicate.]"

    # TODO: Has not been tested!
    if inat["spam"]:
      unit['sourceTags'].append("ADMIN_MARKED_SPAM")
      keywords.append("spam-observation")

    # TODO: Has not been tested!
    if inat["user"]["spam"]:
      unit['sourceTags'].append("ADMIN_MARKED_SPAM")
      keywords.append("spam-user")

    # TODO: Maybe hide obs from suspended users?
#    if inat["user"]["suspended"]:



    # Quality grade
    unitFacts.append({ "fact": "quality_grade", "value": inat['quality_grade'] + "_grade"})
    keywords.append(inat['quality_grade'] + "_grade")


    # Quality tags
    if "research" == inat['quality_grade']:
      unit['sourceTags'].append("COMMUNITY_TAG_VERIFIED")


    # Misc facts
    unitFacts = inatHelpers.appendRootFact(unitFacts, inat, "out_of_range")
    unitFacts = inatHelpers.appendRootFact(unitFacts, inat, "taxon_geoprivacy")
    unitFacts = inatHelpers.appendRootFact(unitFacts, inat, "geoprivacy")
#    unitFacts = inatHelpers.appendRootFact(unitFacts, inat, "context_geoprivacy") # not used anymore?
#    unitFacts = inatHelpers.appendRootFact(unitFacts, inat, "context_user_geoprivacy") # not used anymore?
#    unitFacts = inatHelpers.appendRootFact(unitFacts, inat, "context_taxon_geoprivacy") # not used anymore?
    unitFacts = inatHelpers.appendRootFact(unitFacts, inat, "comments_count")
    unitFacts = inatHelpers.appendRootFact(unitFacts, inat, "num_identification_agreements")
    unitFacts = inatHelpers.appendRootFact(unitFacts, inat, "num_identification_disagreements")
    unitFacts = inatHelpers.appendRootFact(unitFacts, inat, "owners_identification_from_vision")
    unitFacts = inatHelpers.appendRootFact(unitFacts, inat, "oauth_application_id")
    unitFacts = inatHelpers.appendRootFact(unitFacts, inat, "identifications_count")


    # Misc keywords
    keywords = appendKeyword(keywords, inat, "out_of_range")
    keywords = appendKeyword(keywords, inat, "identifications_most_agree")
    keywords = appendKeyword(keywords, inat, "identifications_most_disagree")
    keywords = appendKeyword(keywords, inat, "owners_identification_from_vision")


    # Faves
    if inat["faves_count"] >= 1:
      keywords.append("faved")

    if inat["faves_count"] >= 5:
      keywords.append("many_faved")
    elif inat["faves_count"] >= 3:
      keywords.append("few_faved")


    # Application used to save the obs
    if not inat["oauth_application_id"]:
      inat["oauth_application_id"] = 999 # Fake value for web client

    keywords.append("oauth_" + str(inat["oauth_application_id"]))


    # Coordinates
    # Note that observation can have mappable == false, even though it has coordinates. Example: 87717426 because its has very large error radius
    if inat['mappable']:
      gathering['coordinates'] = inatHelpers.getCoordinates(inat)

    # -------------------------------------
    # Build the multidimensional dictionary

    publicDocument['facts'] = documentFacts
    gathering['facts'] = gatheringFacts
    unit['facts'] = unitFacts

    # Lowercase keywords
    for word in range(len(keywords)):
      keywords[word] = keywords[word].lower()

    publicDocument['keywords'] = keywords


    gathering["units"] = []
    gathering["units"].append(unit)

    publicDocument['gatherings'] = []
    publicDocument['gatherings'].append(gathering)

    dw['publicDocument'] = publicDocument

    # -------------------------------------
    # Get private data for PAP

    # Adds privateDocument only if there is some private data
    if has_private_data or has_private_email:
      # Makes a deep copy of the public document. After this, modifying the public document has no effect on private document.
      privateDocument = copy.deepcopy(publicDocument)

      privateDocument['concealment'] = "PRIVATE"

      # Append 'privatedata' to keywords
      privateDocument["keywords"].append("privatedata")

      # Handle private location and date
      if has_private_data:
        # Add private date
        if hasValue(privateData["observed_on"]):
          privateDocument["gatherings"][0]["eventDate"]["begin"] = privateData["observed_on"]
          privateDocument["gatherings"][0]["eventDate"]["end"] = privateData["observed_on"]

        # Add private coordinates
        if inat['mappable']:
          if hasValue(privateData["private_longitude"]):        
            privateDocument["gatherings"][0]["coordinates"]["lonMin"] = privateData["private_longitude"]
            privateDocument["gatherings"][0]["coordinates"]["lonMax"] = privateData["private_longitude"]
            privateDocument["gatherings"][0]["coordinates"]["latMin"] = privateData["private_latitude"]
            privateDocument["gatherings"][0]["coordinates"]["latMax"] = privateData["private_latitude"]

          if hasValue(privateData["positional_accuracy"]):
            privateDocument["gatherings"][0]["coordinates"]["accuracyInMeters"] = privateData["positional_accuracy"]
          
        # Add private location name
        if hasValue(privateData["private_place_guess"]):
          privateDocument["gatherings"][0]["locality"] = privateData["private_place_guess"]

      # Handle private email
      if has_private_email:
        # Add private email
        privateDocument["gatherings"][0]['facts'].append({ "fact": "email", "value": private_email })
      
      dw['privateDocument'] = privateDocument

    # -------------------------------------
    # Remove any private data from the public document

    # -------------------------------------
    # Finalize

    dwObservations.append(dw)

    # Store last converted observation
    lastUpdateKey = inat["id"]

    print(" -> done ")


  # End for each observations

  # Root elements for DW
  dwRoot = {}
  dwRoot["schema"] = "laji-etl"
  dwRoot["roots"] = dwObservations

  return dwRoot, lastUpdateKey