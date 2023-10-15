from bs4 import BeautifulSoup
import re
import arrow
from application.core.utils.logger import httpLogger, logger
# from core.utils.logger import logger
from application.core.utils.http_client import http_client
import requests


# Factory class for generating Hamilton property objects 
# Accepts an address object. Required address attributes are:
    #   'street_number' (e.g. 73)
    #   'street_name' (e.g. Tisdale)
    #   'street_type_short' (e.g. St) or 'street_type_long' (e.g. Street)
    #   'street_direction_short' (e.g. S) or 'street_direction_long' (South), if applicable
    #   'city' (must be one of Hamilton, Ancaster, Dundas, Flamborough, Glanbrook, or Stoney Creek)
class ls_hamilton_property:
    def __init__(self, address={}):
        self.address = address
        self.location = self.get_location(self.address)
        self.taxes = self.get_taxes(self.address)
        if self.taxes:
            for tax in self.taxes:
                tax = self.check_tax_exempt(tax)
                tax = self.get_tax_assessment_years(tax)
                tax = self.get_tax_levy_years(tax)
        if self.location:
            self.ward = self.get_ward(self.location)
        else:
            self.ward = None
        if self.location:
            self.zoning = self.get_zoning_data(self.location)
        else:
            self.zoning = {}
        if self.location:
            self.temp_use = self.get_temp_use_data(self.location)
        else:
            self.temp_use = {}
        if self.location:
            self.building_permits = self.get_building_permits(self.address)
        else: self.building_permits = []


    # Accepts an address object and returns long/lat in EPSG:4326 and EPSG:3857 coordinates.
    # Required input address attributes:
    #   'street_number'
    #   'street_name'
    #   'street_type_long'
    #   'street_direction_short' or 'street_direction_long' if applicable
    def get_location(self, address):

        # The URL for the City of Hamilton's ArcGIS-powered address search, hosted by Spatial Solutions Inc
        url = "https://spatialsolutions.hamilton.ca/webgis/rest/services/Geocoders/Address_Locator/GeocodeServer/findAddressCandidates"
        # url = "https://httpstat.us/500"

        # Format the address object as a single-line string
        addressString = address['street_number']+" "+address['street_name']+" "+address['street_type_long'] 
        if address.get('street_direction_long') is not None:
            addressString = addressString+" "+address['street_direction_long']
        if address.get('city') is not None:
            addressString = addressString+" "+address['city']

        # Create an empty location object and let's go!
        location = {}

        # Assemble the address string into requests for EPSG:4326 and EPSG:3857 coordinates,
        # along with other required parameters
        requestData4326 = {'SingleLine': addressString, 'f': 'json', 'outSR': '{wkid: 4326}', 'outFields': '*', 'maxLocations': '1'}
        requestData3857 = {'SingleLine': addressString, 'f': 'json', 'outSR': '{wkid: 3857}', 'outFields': '*', 'maxLocations': '1'}

        # Check if a request returns an HTTP error
        try:
            http_client.get(url, params=requestData4326)

        # If it does, log the HTTP error and return nothing
        except requests.exceptions.RequestException as e:
            httpLogger.error(e)
            return location

        # If it doesn't, get the responses
        else:
            response4326 = http_client.get(url, params=requestData4326).json()
            response3857 = http_client.get(url, params=requestData3857).json()

            # If the responses contain candidate results, assemble them into a location object 
            if response4326["candidates"]:
                location['EPSG:4326'] = response4326["candidates"][0]["location"]
                location['EPSG:3857'] = response3857["candidates"][0]["location"]
                logger.debug("Found the location for "+addressString)

            # If they don't, log a warning and return nothing
            else:
                logger.warning("Can't find a location for "+addressString)
            return location


    # Accepts a location object and returns the city ward
    def get_ward(self, location):

        # The URL for the City of Hamilton's ArcGIS-powered ward query service, hosted by Spatial Solutions Inc
        url = "https://spatialsolutions.hamilton.ca/webgis/rest/services/General/Political/MapServer/15/query"
        # url = "https://httpstat.us/500"

        # Assemble the location data into a request, along with other required parameters
        requestData = {
                'f': 'json',
                'outSR': '{wkid:4326}',
                'geometryType': 'esriGeometryPoint',
                'inSR': '{wkid:4326}',
                'geometry': "{'x': "+str(location['EPSG:4326']['x'])+", 'y': "+str(location['EPSG:4326']['y'])+", 'spatialReference': '{'wkid': '4326'}'}",
                'returnIdsOnly': 'true'
            }

        # Check if the request returns an HTTP error
        try:
            http_client.get(url, params=requestData)

        # If it does, log the HTTP error and return nothing
        except requests.exceptions.RequestException as e:
            httpLogger.error(e)
            return None

        # If it doesn't, get the response
        else:
            response = http_client.get(url, params=requestData)

            # If the reponse contains a ward object, return it
            if response.json()['objectIds'] != None:
                ward = str(response.json()['objectIds'][0])
                logger.debug("Found ward "+ward)
                return ward
            else:
                logger.warning("Couldn't find the ward")
                return None


    # Accepts a location object and returns zoning data
    def get_zoning_data(self, location):

        # The query URL for the ArcGIS zoning map service, hosted for the city by Spatial Solutions
        url = "https://spatialsolutions.hamilton.ca/webgis/rest/services/General/Zoning/MapServer/dynamicLayer/query"
        # url = "https://httpstat.us/500"

        # Assemble the location object into query request data, including some other required parameters
        # We will use this request to check to see if zoning is returned for this location
        checkRequestData = {
                'f': 'json',
                'outSR': '{wkid:4326}',
                'geometryType': 'esriGeometryPoint',
                'inSR': '{wkid:4326}',
                'geometry': "{'x': "+str(location['EPSG:4326']['x'])+", 'y': "+str(location['EPSG:4326']['y'])+", 'spatialReference': '{'wkid': '4326'}'}",
                'returnIdsOnly': 'true',
                'layer': "{'source':{'type':'mapLayer','mapLayerId': '9'}}"
        }

        # Assemble the location object into query request data, including some other required parameters
        # We will use this request to retrieve the zoning data if the check comes back positive
        requestData = {
            'f': 'json',
            'returnGeometry': 'false',
            'outSR': '{wkid:4326}',
            'geometryType': 'esriGeometryPoint',
            'inSR': '{wkid:4326}',
            'geometry': "{'x': "+str(location['EPSG:4326']['x'])+", 'y': "+str(location['EPSG:4326']['y'])+", 'spatialReference': '{'wkid': '4326'}'}",
            'layer': "{'source':{'type':'mapLayer','mapLayerId': '9'}}",
            'outFields': 'ZONING_CODE,ZONING_DESC,PARENT_BY_LAW_NUMBER,PARENT_BY_LAW_URL,BY_LAW_NUMBER,BY_LAW_URL,EXCEPTION1,EXCEPTION1_BYLAW,EXCEPTION1_URL,HOLDING1,HOLDING1_BYLAW,HOLDING1_URL,HOLDING2,HOLDING2_BYLAW,HOLDING2_URL,HOLDING3,HOLDING3_BYLAW,HOLDING3_URL,COMMUNITY,ZONING_MAP,COUNCIL_APP_DATE,ZONING_FILE,OMB_NUMBER,OMB_CASE_NUMBER,OPA_NUMBER,URBAN_RURAL_SETTLE,FINALBINDING_DATE,SHAPE.AREA,SHAPE.LEN'
        }

        # Create an empty zoning object and off we go!
        zoning = {}

        # Check if the request returns an HTTP error
        try:
            response = http_client.get(url, params=checkRequestData)

        # If it does, log the HTTP error and return an empty zoning data object
        except requests.exceptions.RequestException as e:
            httpLogger.error(e)
            return zoning

        # If it doesn't, check to see if the response contains zoning data
        else:
            checkResponse = http_client.get(url, params=checkRequestData).json()
            
            # If it does, return the zoning data
            if checkResponse['objectIds'] != None:
                zoning = http_client.get(url, params=requestData).json()['features'][0]['attributes']
                logger.debug("Found zoning data")
                return zoning

            # If it doesn't, log a warning and return the empty zoning object
            else:
                logger.warning("Could not find zoning data")
                return zoning


    # Accepts a location object and returns any temporary use applications
    def get_temp_use_data(self, location):

        # The query URL for the ArcGIS zoning map service, hosted for the city by Spatial Solutions
        url = "https://spatialsolutions.hamilton.ca/webgis/rest/services/General/Zoning/MapServer/dynamicLayer/query"
        # url = "https://httpstat.us/500"

        # Assemble the location object into query request data, including some other required parameters
        # We will use this request to check to see if temp use data is returned for this location
        checkRequestData = {
                'f': 'json',
                'outSR': '{wkid:4326}',
                'geometryType': 'esriGeometryPoint',
                'inSR': '{wkid:4326}',
                'geometry': "{'x': "+str(location['EPSG:4326']['x'])+", 'y': "+str(location['EPSG:4326']['y'])+", 'spatialReference': '{'wkid': '4326'}'}",
                'returnIdsOnly': 'true',
                'layer': "{'source':{'type':'mapLayer','mapLayerId': '20'}}"
        }

        # Assemble the location object into query request data, including some other required parameters
        # We will use this request to retrieve the temp use data if the check comes back positive
        requestData = {
                'f': 'json',
                'returnGeometry': 'false',
                'outSR': '{wkid:4326}',
                'geometryType': 'esriGeometryPoint',
                'inSR': '{wkid:4326}',
                'geometry': "{'x': "+str(location['EPSG:4326']['x'])+", 'y': "+str(location['EPSG:4326']['y'])+", 'spatialReference': '{'wkid': '4326'}'}",
                'layer': "{'source':{'type':'mapLayer','mapLayerId': '9'}}",
                'outFields': 'OBJECTID,ID,ZONING_CODE,ZONING_DESC,PARENT_BY_LAW_NUMBER,PARENT_BY_LAW_URL,BY_LAW_NUMBER,BY_LAW_URL,EXCEPTION1,EXCEPTION1_BYLAW,EXCEPTION1_URL,HOLDING1,HOLDING1_BYLAW,HOLDING1_URL,EXCEPTION2,EXCEPTION2_BYLAW,EXCEPTION2_URL,HOLDING2,HOLDING2_BYLAW,HOLDING2_URL,EXCEPTION3,EXCEPTION3_BYLAW,EXCEPTION3_URL,HOLDING3,HOLDING3_BYLAW,HOLDING3_URL,COMMUNITY,ZONING_MAP,COUNCIL_APP_DATE,ZONING_FILE,OMB_NUMBER,OMB_CASE_NUMBER,OPA_NUMBER,URBAN_RURAL_SETTLE,FINALBINDING_DATE,SHAPE.AREA,SHAPE.LEN'
        }

        # Create an empty temp use object and off we go!
        temp_use = {}

        # Check if the request returns an HTTP error
        try:
            response = http_client.get(url, params=checkRequestData)

        # If it does, log the HTTP error and return an empty temp use data object
        except requests.exceptions.RequestException as e:
            httpLogger.error(e)
            return temp_use

        # If it doesn't, check to see if the response contains temp use data
        else:
            checkResponse = http_client.get(url, params=checkRequestData).json()

            # If it does, return the temp use data
            if checkResponse['objectIds'] != None:
                temp_use = http_client.get(url, params=requestData).json()['features'][0]['attributes']
                logger.debug("Found temp use data")
                return temp_use

            # If it doesn't, log a warning and return the empty temp use object
            else:
                logger.warning("Could not find temp use data")
                return temp_use


    # Accepts an address object and returns a list of any building permits
    def get_building_permits(self, address):

        # Create an empty building permits list
        building_permits = []

        # The URL for retrieving a session cookie from the Eplans application
        cookieURL = "https://eplans.hamilton.ca/EPlansPortal/sfjsp?interviewID=Welcome"

        # Extract the raw session cookie from the http client's 'cookies' object
        cookies = http_client.get(cookieURL, verify=False).cookies.get_dict()
        cookie = "JSESSIONID="+cookies["JSESSIONID"]
        http_client.cookies.clear()

        # The URL for the application's session manager 
        url = "https://eplans.hamilton.ca/EPlansPortal/sfjsp"

        # Assemble the request headers required to get a session 
        headers = {"Cookie": cookie, "Host": "eplans.hamilton.ca"}

        # Check if the request for a session returns an HTTP error
        try:
            session_response = http_client.post(url, data = {"e_1482930323468": "onclick"}, headers = headers, verify = False)

        # If it does, log the HTTP error and return an empty building permits list
        except requests.exceptions.RequestException as e:
            httpLogger.error(e)
            return building_permits

        # If it doesn't, time to query the app for permits
        else:

            # Construct an address string from the address object
            if address.get('street_direction_long') is not None:
                addressString = address['street_number']+';'+address['city']+';'+address['street_name']+';'+address['street_direction_long']+';'
            else:
                addressString = address['street_number']+';'+address['city']+';'+address['street_name']+';'

            # Assemble the address string along with other required post parameters into the query request
            request_data = {
                    "d_1536239857790": "buildingnewconstructionpermit",
                    "d_1537469348077": "address",
                    "d_1536259115820": addressString,
                    "e_1536239857797": "onclick"
                }

            # Check if the request for build permits returns an HTTP error
            try:
                http_client.post(url, data = request_data, headers = headers, verify = False)

            # If it does, log the HTTP error and return an empty building permits list
            except requests.exceptions.RequestException as e:
                httpLogger.error(e)
                return building_permits

            # If it doesn't, get the response and pass it to BeautifulSoup
            else:
                response = BeautifulSoup(http_client.post(url, data = request_data, headers = headers, verify = False).text, "html.parser")

                # If there are building permit records on the page
                if response.find("div", {'class': 'panel-title'}):

                    # Append them to the building permits list
                    for row in response.find("span", text = re.compile("Application #")).parent.parent.parent.parent.tbody.find_all("tr"):
                        permit = {}
                        permit["application_number"] = row.find_all("td")[0].div.contents[0].strip().replace(" ", "")
                        permit["description"] = row.find_all("td")[1].div.contents[0].strip()
                        permit["status"] = row.find_all("td")[3].div.contents[0].strip()
                        building_permits.append(permit)
                    logger.debug("Found building permits for "+addressString)

                # If there are no records, log a warning
                else:
                    logger.debug("Could not find building permits for "+addressString)

                # Return the building permits object
                return building_permits

    # Accepts an address object and returns a list of tax objects with roll number attributes, ready to be populated
    def get_taxes(self, address):

        # Create an empty list to add tax objects to
        taxes = []

        # The query URL for the property inquiry application
        url = "http://oldproperty.hamilton.ca/property-inquiry_noborders/list.asp"
        # url = "https://httpstat.us/500"

        # Create the address string from the street name and the short street type, e.g. 73 Tisdale St 
        # The property inquiry app chokes on long street types, e.g. 73 Tisdale Street
        addressString = address['street_name']+" "+address['street_type_short']

        # Check to see if the street has a direction, and if so append the short version, e.g. 73 Tisdale St S
        # The property inquiry app chokes on long street directions, e.g 73 Tisdale S South
        if address.get('street_direction_short') is not None:
            addressString = addressString+" "+address['street_direction_short']

        # Map the city attribute to a 'community' value that the application accepts
        if 'city' in address:
            if address['city'] == "Hamilton":
                community = "ham010081"
            else:
                if address['city'] == "Ancaster":
                    community = "anc140140"
                else:
                    if address['city'] == "Dundas":
                        community = "dun260260"
                    else:
                        if address['city'] == "Flamborough":
                            community = "fla301303"
                        else:
                            if address['city'] == "Glanbrook":
                                community = "gla901902"
                            else:
                                if address['city'] == "Stoney Creek":
                                    community = "scr003003"
                                else:
                                    community = "all000999"
        else:
            community = "all000999"

        # Append the address string along with other required parameters into the request body
        requestData = {
                "stnum": address['street_number'],
                "address": addressString,
                "community": community,
                "B1": "Search"
            }

        # Check if the request returns an HTTP error
        try:
            response = http_client.post(url, requestData)

        # If it does, log the HTTP error and return nothing
        except requests.exceptions.RequestException as e:
            httpLogger.error(e)
            return taxes

        # If it doesn't, convert the HTML response to text and parse it with BeautifulSoup
        else:
            response = BeautifulSoup(http_client.post(url, requestData).text, "html.parser")

            # If the response includes a list of properties, there is more than one roll number associated with the address
            # That means we'll need to populate the taxes list with more than one tax object
            if response.find("p", text = re.compile("Property List")):
                logger.debug ("Found more than one roll number for "+address['street_number']+" "+addressString)

                # Parse out the roll numbers and return them in a list    
                roll_numbers = [href.get_text().strip() for href in response.find_all(href=re.compile("detail.asp"))]

                # For each roll number in the list, append a tax object to the taxes list and add the roll number as an attribute
                for r in roll_numbers:
                    taxes.append({"roll_number": r})

                # return the taxes list
                return taxes

            # If the response doesn't contain a list of properties, check to see if the response contains a single roll number
            else:
                if response.find("b", text = re.compile("Roll Number")):

                    # If it does, return it
                    roll_number = response.find("b", text = re.compile("Roll Number")).parent.parent.next_sibling.next_sibling.contents[0].strip() 
                    logger.debug("Found the roll number for "+address['street_number']+" "+addressString)
                    taxes = [{"roll_number": roll_number}]
                    return taxes

                # If it doesn't, log a warning and return nothing
                else:
                    logger.warning("No roll number for "+address['street_number']+" "+addressString)
                    return taxes


    # Accepts a tax object and appends an is_tax_exempt attribute
    # Tax object must have a a roll number attribute
    def check_tax_exempt(self, tax):
 
        # The URL for querying by roll number against the Property Inquiry application 
        url = "http://oldproperty.hamilton.ca/property-inquiry_noborders/detail.asp?qryrollno="+tax['roll_number']
        # url = "https://httpstat.us/500"

        # Check if the request returns an HTTP error
        try:
            response = http_client.get(url)

        # If it does, log the HTTP error and return nothing
        except requests.exceptions.RequestException as e:
            httpLogger.error(e)
            return tax

        # If it doesn't, parse the response with BeautifulSoup and check to see if it's exempt
        else:
            if self.fetch(url).find_all("td", {"class": "bodycopy"}, text = re.compile("Exempt")):

                # If it is, set is_tax_exempt to True, and return tax object
                logger.debug(tax['roll_number']+" is tax exempt")
                tax["is_tax_exempt"] = True
                return tax

            # If it isn't, set is_tax_exempt to False, and return tax object
            else:
                logger.debug(tax['roll_number']+" is not tax exempt")
                tax["is_tax_exempt"] = False
                return tax


    # Accepts a tax object and appends a list of tax assessment years
    # Tax object must have a a roll number attribute
    def get_tax_assessment_years(self, tax):

        # Create an empty list to populate with tax assessment years
        assessment_years = []

        # URL for querying Property Inquiry application by roll number
        url = "http://oldproperty.hamilton.ca/property-inquiry_noborders/detail.asp?qryrollno="+tax['roll_number']
        # url = "https://httpstat.us/500"

        # Check if the request returns an HTTP error
        try:
            response = http_client.get(url)

        # If it does, log the HTTP error and return nothing
        except requests.exceptions.RequestException as e:
            httpLogger.error(e)
            tax["assessment_years"] = assessment_years
            return tax

        # If it doesn't, convert the HTML response to text and parse it with BeautifulSoup
        else:

            # For each row in the tax assessment table, create a record
            for row in self.fetch(url).find("b", text = re.compile(r"Current Year Assessment")).parent.parent.parent.parent.find_all("tr"):
                if not (row.find(text = re.compile("Year")) or row.find(text = re.compile("Total Assessment")) or row.find(text = re.compile("Current Year Assessment"))):
                    assessment_year = {}
                    assessment_year["year"] = row.find_all("td")[0].contents[0].strip()
                    assessment_year["class"] = row.find_all("td")[1].contents[0].strip()
                    assessment_year["description"] = row.find_all("td")[2].contents[0].strip()
                    assessment_year["amount"] = row.find_all("td")[3].contents[0].strip().replace(",", "")
                    
                    # Append the record to the assessment years list
                    assessment_years.append(assessment_year)

            # Add the assessment years attribute to the tax object, and return it
            tax["assessment_years"] = assessment_years
            logger.debug("Found tax assessment years for roll number "+tax['roll_number'])
            return tax


    # Accepts a tax object and appends a list of tax levy years
    # Tax object must have a a roll number attribute
    def get_tax_levy_years(self, tax):

        # Create an empty list to populate with tax levy years
        levy_years = []

        # URL for querying Property Inquiry application by roll number
        url = "http://oldproperty.hamilton.ca/property-inquiry_noborders/detail.asp?qryrollno="+tax['roll_number']
        # url = "https://httpstat.us/500"

        # Check if the request returns an HTTP error
        try:
            response = http_client.get(url)

        # If it does, log the HTTP error and return nothing
        except requests.exceptions.RequestException as e:
            httpLogger.error(e)
            tax["levy_years"] = levy_years
            return tax

        # If it doesn't, convert the HTML response to text and parse it with BeautifulSoup
        else:

            # Check to see if the property is tax exempt
            if not tax.get('is_tax_exempt'):

                # If not, for each year in the tax levy table, add a year object
                for row in self.fetch(url).find(text = re.compile("Tax Levy History")).parent.parent.parent.parent.parent.find_all("tr"):
                    if not (row.find(text = re.compile("Tax Levy History")) or row.find(text = re.compile("Year"))):
                        levy_year = {}
                        levy_year["year"] = row.find_all("td")[1].contents[0].strip()

                        # Add an amount object to the year object
                        levy_year['amount'] = {}

                        # Add the total amount for the year
                        levy_year["amount"]['total'] = row.find_all("td")[2].contents[0].strip().replace(",", "")

                        # Append the record to the levy years list
                        levy_years.append(levy_year) 

                # For each row in the Breakdown table, add municipal and education levy attributes to the amount 
                # record for the first levy year (The first year will always be the current year, for which the app 
                # breaks out amounts)
                for row in self.fetch(url).find(text = re.compile("Breakdown")).parent.parent.parent.parent.parent.find_all("tr"):
                    if not (row.find(text = re.compile("Breakdown")) or row.find(text = re.compile("Type")) or row.find(text = re.compile("Total"))):
                        levy_years[0]['amount'][row.find_all("td")[0].contents[0].strip().replace(" ", "_").lower()] = row.find_all("td")[1].contents[0].strip().replace(",", "")

                # Add an empty installments list to first levy year object (The first year will always be the current year, 
                # for which the app provides a table of installments)
                levy_years[0]['installments'] = []

                # For each row in the Installments table, append an installment object to the list (inc. date and amount)
                for row in self.fetch(url).find_all(text = re.compile("Instalments"))[0].parent.parent.parent.parent.parent.find_all("tr"):
                    if not (row.find(text = re.compile("Instalments")) or row.find(text = re.compile("Amount")) or row.find(text = re.compile("Total"))):
                        levy_years[0]['installments'].append({'date': arrow.get(row.find_all("td")[1].contents[0].strip(), 'MMMM\xa0D,\xa0YYYY').format('MM/DD/YYYY'), 'amount': row.find_all("td")[2].contents[0].strip().replace(",", "")})

                # Add the levy years attribute to the tax object, and return it
                tax["levy_years"] = levy_years
                logger.debug("Found tax levy years for roll number "+tax['roll_number'])
                return tax


# -- UTILITY FUNCTIONS --


    # Makes a get request and returns the HTML response to the BeautifulSoup parser
    def fetch(self, url):
        return(BeautifulSoup(http_client.get(url).text, "html.parser"))
