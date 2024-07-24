
import math
import re
import pandas

"""
def appendFact(factsList, factLabel, factValue = False):
  if factValue: # Checks if value is truthy
    factsList.append({ "fact": factLabel, "value": factValue })

  return factsList
"""


# Define email validation function
def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))


# Define function to check if a string is empty or starts with a space
def is_valid_string(s):
  return bool(s) and not s.startswith(' ')


def load_private_emails():
  print("Loading private emails")
  private_user_data = pandas.read_csv("./privatedata/inaturalist-suomi-20-users.csv", sep=',') 

#  print(f"Loaded { len(private_user_data.index) } rows")

  # Ensure both 'login' and 'email' are strings
  private_user_data['login'] = private_user_data['login'].astype(str)
  private_user_data['email'] = private_user_data['email'].astype(str)

  # Filter rows with valid email addresses and non-empty logins
  filtered_df = private_user_data[private_user_data['email'].apply(is_valid_email) & private_user_data['login'].apply(is_valid_string)]

  # Select columns and create a dictionary
  private_user_emails = filtered_df[['login', 'email']].set_index('login')['email'].to_dict()

  print(f"Loaded { len(private_user_emails) } email addresses")

  return private_user_emails


# Extracts and validates atlascode from text string
# Returns None if no valid atlascode found
# Dev version of this function is on the file atlascode.py
def extractAtlasCode(text):
    if None == text:
      return None

    numbers = ["0","1","2","3","4","5","6","7","8","9"]

    # to lowercase
    text = text.lower()

    # Check if text contains atlas keyword
    try:
        index = text.index("atl:")
    except ValueError:
        return None
    else:
        text = text.replace("atl: ", "atl:")

        start = index + 4
        end = start + 2
        atlasCode = text[start:end]

        # If code length is 2, and if trailing char is not a number, remove it 
        if len(atlasCode) == 2:
            trailingChar = atlasCode[1:2]
            if not trailingChar in numbers:
                atlasCode = atlasCode[0:1]

        # If char after atlascode is number, it's probably an error
#        charAfterAtlasCode = text[end:(end + 1)]
#        if charAfterAtlasCode in numbers:
#            print("Char after atlascode is number: " + text)

    # Remove trailing zero
    atlasCode = atlasCode.strip("0")

    allowedAtlasCodes = ["1","2","3","4","5","6","7","8","61","62","63","64","65","66","71","72","73","74","75","81","82"]

    print(" ATLASCODE: " + atlasCode)
    # Check if code is allowed
    if atlasCode in allowedAtlasCodes:
        return atlasCode
    else:
        print(" Disallowed atlascode skipped: " + atlasCode, end = " ")
        return None


def appendRootFact(factsList, inat, factName):
  # Handles only keys directly under root of inat

  if factName in inat: # Checks if key exists
    if inat[factName]: # Checks if value is truthy
      factsList.append({ "fact": factName, "value": inat[factName]} )

  return factsList


def decimalFloor(n, decimals=1):
  multiplier = 10 ** decimals
  return float(math.floor(n * multiplier) / multiplier)


def getCoordinates(inat):

  coord = {}
  coord['type'] = "WGS84";

  # TODO: observation without coordinates

  # Obscured observation
  if inat['obscured']: # Alternative: ("obscured" == geoprivacy || "obscured" = taxon_geoprivacy)
    
    # Creates a 0.2*0.2 degree box around the observation, so that corner first decimal digit is even-numbered.

    lonRaw = inat['geojson']['coordinates'][0]
    lonFirstDigit = int(str(lonRaw).split('.')[1][0])
    if lonFirstDigit % 2 == 0: # even
      coord['lonMin'] = decimalFloor(lonRaw)
      coord['lonMax'] = decimalFloor((lonRaw + 0.2))
    else:
      coord['lonMin'] = decimalFloor((lonRaw - 0.1))
      coord['lonMax'] = decimalFloor((lonRaw + 0.1))

    latRaw = inat['geojson']['coordinates'][1]
    latFirstDigit = int(str(latRaw).split('.')[1][0])
    if latFirstDigit % 2 == 0: # even
      coord['latMin'] = decimalFloor(latRaw)
      coord['latMax'] = decimalFloor((latRaw + 0.2))
    else:
      coord['latMin'] = decimalFloor((latRaw - 0.1))
      coord['latMax'] = decimalFloor((latRaw + 0.1))

#    coord['accuracyInMeters'] = "" # Accuracy not set for obscured obs, since DW calculates it by itself from bounding box

  # Non-obscured observation
  else:
    lon = round(inat['geojson']['coordinates'][0], 5)
    lat = round(inat['geojson']['coordinates'][1], 5)

    if not inat['positional_accuracy']:
      accuracy = 100; # Default for missing values. Mobile app often leaves the value empty, even if the coordinates are accurate.
    elif inat['positional_accuracy'] < 10:
      accuracy = 10 # Minimum value
    else:
      accuracy = round(inat['positional_accuracy'], 0) # Round to one meter

    coord['accuracyInMeters'] = accuracy

    coord['lonMin'] = lon;
    coord['lonMax'] = lon;
    coord['latMin'] = lat;
    coord['latMax'] = lat;  

  return coord


def convertTaxon(taxon):
  convert = {}

  # Conversions from -> to
  convert['Life'] = "Biota"
  convert['unknown'] = "Biota"
  convert['Elämä'] = "Biota" # Is this needed?
  convert['tuntematon'] = "Biota" # Is this needed?

  convert['Taraxacum officinale'] = "Taraxacum"
  convert['Alchemilla vulgaris'] = "Alchemilla"
  convert['Pteridium aquilinum'] = "Pteridium pinetorum"

  # kevätleinikit/toukoleinikit
  convert['Ranunculus cassubicus'] = "Ranunculus cassubicus -ryhmä"
  convert['Ranunculus auricomus'] = "Ranunculus auricomus -ryhmä s. lat."

  convert['Bombus lucorum-complex'] = "Bombus lucorum coll."
  convert['Chrysoperla carnea-group'] = "Chrysoperla"
  convert['Potentilla argentea'] = "Potentilla argentea -ryhmä"
  convert['Chenopodium album'] = "Chenopodium album -ryhmä"
  convert['Imparidentia'] = "Heterodonta" # hieta- ja liejusimpukan alin yhteinen taksoni
  convert['Canis familiaris'] = "Canis lupus familiaris" # koira
  convert['Anguis'] = "Anguis colchica" # vaskitsan erilaiset lajikäsitteet tulkitaan A. colchicaksi (1/2024)
  convert['Monotropa'] = "Hypopitys"
  convert['Monotropa hypopitys'] = "Hypopitys monotropa" # kangasmäntykukka
  convert['Monotropa hypopitys ssp. hypophegea'] = "Hypopitys hypophegea" # kaljumäntykukka


  if not taxon: # Empty, False, Null/None
    return ""  
  elif taxon in convert:
    return convert[taxon]
  else:
    return taxon


def summarizeAnnotation(annotation):
  """
  Annotations describe three attributes (see them below.)

  The logic is complicated, and there's no official documentation about it.
  - Someone creates an observation.
  - Someone creates an annotation for an attribute.
  - Someone adds a value to that attribute.
  - Anyone can vote for or agains that value, but cannot create a competing value.

  In the API, vote_score shows the outcome of the voting. positive=agree, 0=tie, negative=disagree

  Attributes (= keys):
  1=Life Stage, 9=Sex, 12=Flowers and Fruit (Plant Phenology), 17=Live or dead, 36=Leaves

  Values:
  Life Stage: 2=Adult, 3=Teneral, 4=Pupa, 5=Nymph, 6=Larva, 7=Egg, 8=Juvenile, 16=Subimago
  Sex: 10=Female, 11=Male
  Flowers and Fruit: 13=Flowering, 14=Fruiting, 15=Budding, 21=No flowers or fruit
  Leaves: 37=Opening leaves, 38=Green leaves, 39=Colored leaves, 40=No livng leaves
  Live or dead: 18=Live, 19=Dead, 20=Cannot be identified

  See in main conversion script how the result is submitted to DW.

  See more at https://forum.inaturalist.org/t/how-to-use-inaturalists-search-urls-wiki/63
  """

  key = annotation["controlled_attribute_id"]
  value = annotation["controlled_value_id"]
  vote_score = annotation["vote_score"]

  if 2 == value:
    key = "lifeStage"
    value = "ADULT"
  elif 4 == value:
    key = "lifeStage"
    value = "PUPA"
  elif 5 == value:
    key = "lifeStage"
    value = "NYMPH"
  elif 6 == value:
    key = "lifeStage"
    value = "LARVA"
  elif 7 == value:
    key = "lifeStage"
    value = "EGG"
  elif 8 == value:
    key = "lifeStage"
    value = "JUVENILE"
  elif 16 == value:
    key = "lifeStage"
    value = "SUBIMAGO"
  elif 13 == value:
    key = "lifeStage"
    value = "FLOWER"
  elif 10 == value:
    key = "sex"
    value = "FEMALE"
  elif 11 == value:
    key = "sex"
    value = "MALE"
  elif 18 == value:
    key = "dead"
    value = False
  elif 19 == value:
    key = "dead"
    value = True
  else:
    pass


  if vote_score >= 1:
    return key, value

  elif vote_score <= -1:
#    print("Annotation " + str(key) + " = " + str(value) + " was voted against by " + str(vote_score))
    return "keyword", "annotation_against"

  elif 0 == vote_score:
#    print("Annotation " + str(key) + " = " + str(value) + " vote tied")
    return "keyword", "annotation_tie"


def getProxyUrl(squareUrl, imageSize):
  url = squareUrl.replace("square", imageSize)

  # TODO: User full URL when CC-images moved to free bucket 
  return url

  '''
  # Rudimentatry test that URL is expected.
  # TODO: Test for changes in the URL's
  if not url.startswith("https://inaturalist-open-data.s3.amazonaws.com/photos/"):
    print("Skipping image with unexpected url ", url)
    return ""

  splitUrl = url.split("/photos/")
  proxyUrl = "https://proxy.laji.fi/inaturalist/photos/" + splitUrl[1]
#  print(proxyUrl)

#  url = url.replace("https://static.inaturalist.org/photos/", "https://proxy.laji.fi/inaturalist/photos/")

  return proxyUrl
  '''


