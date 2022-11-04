from bs4 import BeautifulSoup
import re
import arrow
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import http


DEFAULT_TIMEOUT = 5 # seconds
HTTP_DEBUG_LEVEL = 0
# Retry strategy
retries = Retry(total=1, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])

# Create a custom requests object
http_client = requests.Session()
# Set the debug level
http.client.HTTPConnection.debuglevel = HTTP_DEBUG_LEVEL
# Call back if the server responds with an HTTP error code
assert_status_hook = lambda response, *args, **kwargs: response.raise_for_status()
http_client.hooks["response"] = [assert_status_hook]
# Extend the HTTP adapter so that it provides a default timeout that you can override when constructing the client
class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        self.timeout = DEFAULT_TIMEOUT
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        super().__init__(*args, **kwargs)
    def send(self, request, **kwargs):
        timeout = kwargs.get("timeout")
        if timeout is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)
# Mount the extended timeout adaptor with the retry strategy for all requests
http_client.mount("https://", TimeoutHTTPAdapter(max_retries=retries))
http_client.mount("http://", TimeoutHTTPAdapter(max_retries=retries))


class ham_prop:
	def __init__(self, address={}, roll_number=""):
		if address:
			self.address = address
			self.address = self.validate_address(self.address)
			self.roll_number = self.get_roll_number(self.address)
		if roll_number:
			self.roll_number = roll_number
			self.roll_number = self.validate_roll_number(self.roll_number)
			self.address = self.get_address(self.roll_number)
			self.address = self.validate_address(self.address)
		self.location = self.get_location(self.address)
		self.ward = self.get_ward(self.location)
		if self.roll_number:
			self.tax_assessment_years = self.get_tax_assessment_years(self.roll_number)
		self.tax_levy_years = self.get_tax_levy_years(self.roll_number)
		self.tax_breakdown_years = self.get_tax_breakdown_years(self.roll_number)
		self.tax_installment_years = self.get_tax_installment_years(self.roll_number)
		self.zoning = self.get_zoning_data(self.location)
		self.temp_use = self.get_temp_use_data(self.location)
		self.building_permit = self.get_building_permit_apps(self.address)

	def validate_address(self, address):
	# Accepts a Hamilton address object, validates the address, and appends any additionally available attributes.
	# Required input attributes are:
	# 	'street_number'
	# 	'street_name'
	# 	'street_type_short' or 'street_type_long'
	# 	'street_direction_short' or 'street_direction_long' if applicable
		if self.address.get('street_type_short') is not None:
			if address.get('street_type_long') is None:
				address['street_type_long'] = self.expand_address_type(address['street_type_short'])
		if address.get('street_type_long') is not None:
			if address.get('street_type_short') is None:
				address['street_type_short'] = self.contract_address_type(address['street_type_long'])
		if address.get('street_direction_short') is not None:
			if address.get('street_direction_long') is None:
				address['street_direction_long'] = self.expand_address_direction(address['street_direction_short'])
		if address.get('street_direction_long') is not None:
			if address.get('street_direction_short') is None:
				address['street_direction_short'] = self.contract_address_direction(address['street_direction_long'])
		url = "https://spatialsolutions.hamilton.ca/webgis/rest/services/Geocoders/Address_Locator/GeocodeServer/findAddressCandidates"
		addressString = address['street_number']+" "+address['street_name']+" "+address['street_type_long']	
		if address.get('street_direction_long') is not None:
			addressString = addressString+" "+address['street_direction_long']
		if address.get('city') is not None:
			addressString = addressString+" "+address['city']
		requestData = {'SingleLine': addressString, 'f': 'json', 'outSR': '{wkid: 4326}', 'outFields': '*', 'maxLocations': '1'}
		response = http_client.get(url, params=requestData).json()
		if response['candidates']:
			print("Validated "+str(address)+"! \n")
			address['validated'] = 'True'
			if address.get('city') is None:
				address['city'] = response["candidates"][0]["attributes"]["City"]
			if address.get('neighborhood') is None:
				address['neighborhood'] = response["candidates"][0]["attributes"]["Nbrhd"]
		else:
			print("Could not validate "+str(address)+"! \n")
		return address

	def expand_address_type(self, address):
		if re.search(r'\bAVE\b', address):
			return re.sub(r'\bAVE\b', 'AVENUE', address)
		if re.search(r'\bAve\b', address):
			return re.sub(r'\bAve\b', 'Avenue', address)
		if re.search(r'\bBLVD\b', address):
			return re.sub(r'\bBLVD\b', 'BOULEVARD', address)
		if re.search(r'\bBlvd\b', address):
			return re.sub(r'\bBlvd\b', 'Boulevard', address)
		if re.search(r'\bCIR\b', address):
			return re.sub(r'\bCIR\b', 'CIRCLE', address)
		if re.search(r'\bCir\b', address):
			return re.sub(r'\bCir\b', 'Circle', address)
		if re.search(r'\bCRT\b', address):
			return re.sub(r'\bCRT\b', 'COURT', address)
		if re.search(r'\bCrt\b', address):
			return re.sub(r'\bCrt\b', 'Court', address)
		if re.search(r'\bCRES\b', address):
			return re.sub(r'\bCRES\b', 'CRESCENT', address)
		if re.search(r'\bCres\b', address):
			return re.sub(r'\bCres\b', 'Crescent', address)
		if re.search(r'\bDR\b', address):
			return re.sub(r'\bDR\b', 'DRIVE', address)
		if re.search(r'\bDr\b', address):
			return re.sub(r'\bDr\b', 'Drive', address)
		if re.search(r'\bGDN\b', address):
			return re.sub(r'\bGDN\b', 'GARDEN', address)
		if re.search(r'\bGdn\b', address):
			return re.sub(r'\bGdn\b', 'Garden', address)
		if re.search(r'\bHTS\b', address):
			return re.sub(r'\bHTS\b', 'HEIGHTS', address)
		if re.search(r'\bHts\b', address):
			return re.sub(r'\bHts\b', 'Heights', address)
		if re.search(r'\bHWY\b', address):
			return re.sub(r'\bHWY\b', 'HIGHWAY', address)
		if re.search(r'\bHwy\b', address):
			return re.sub(r'\bHwy\b', 'Highway', address)
		if re.search(r'\bPKY\b', address):
			return re.sub(r'\bPKY\b', 'PARKWAY', address)
		if re.search(r'\bPky\b', address):
			return re.sub(r'\bPky\b', 'Parkway', address)
		if re.search(r'\bPL\b', address):
			return re.sub(r'\bPL\b', 'PLACE', address)
		if re.search(r'\bPl\b', address):
			return re.sub(r'\bPl\b', 'Place', address)
		if re.search(r'\bRD\b', address):
			return re.sub(r'\bRD\b', 'ROAD', address)
		if re.search(r'\bRd\b', address):
			return re.sub(r'\bRd\b', 'Road', address)
		if re.search(r'\bSQ\b', address):
			return re.sub(r'\bSQ\b', 'SQUARE', address)
		if re.search(r'\bSq\b', address):
			return re.sub(r'\bSq\b', 'Square', address)
		if re.search(r'\bST\b', address):
			return re.sub(r'\bST\b', 'STREET', address)
		if re.search(r'\bSt\b', address):
			return re.sub(r'\bSt\b', 'Street', address)
		if re.search(r'\bTERR\b', address):
			return re.sub(r'\bTERR\b', 'TERRACE', address)
		if re.search(r'\bTerr\b', address):
			return re.sub(r'\bTerr\b', 'Terrace', address)
		if re.search(r'\bEXWY\b', address):
			return re.sub(r'\bEXWY\b', 'EXPRESSWAY', address)
		if re.search(r'\bExwy\b', address):
			return re.sub(r'\bExwy\b', 'Expressway', address)
		else:
			return address

	def contract_address_type(self, address):
		if re.search(r'\bAVENUE\b', address):
			return re.sub(r'\bAVENUE\b', 'AVE', address)
		if re.search(r'\bAvenue\b', address):
			return re.sub(r'\bAvenue\b', 'Ave', address)
		if re.search(r'\bBOULEVARD\b', address):
			return re.sub(r'\bBOULEVARD\b', 'BLVD', address)
		if re.search(r'\bBoulevard\b', address):
			return re.sub(r'\bBoulevard\b', 'Blvd', address)
		if re.search(r'\bCIRCLE\b', address):
			return re.sub(r'\bCIRCLE\b', 'CIR', address)
		if re.search(r'\bCircle\b', address):
			return re.sub(r'\bCircle\b', 'Cir', address)
		if re.search(r'\bCOURT\b', address):
			return re.sub(r'\bCOURT\b', 'CRT', address)
		if re.search(r'\bCourt\b', address):
			return re.sub(r'\bCourt\b', 'Crt', address)
		if re.search(r'\bCRESCENT\b', address):
			return re.sub(r'\bCRESCENT\b', 'CRES', address)
		if re.search(r'\bCrescent\b', address):
			return re.sub(r'\bCrescent\b', 'Cres', address)
		if re.search(r'\bDRIVE\b', address):
			return re.sub(r'\bDRIVE\b', 'DR', address)
		if re.search(r'\bDrive\b', address):
			return re.sub(r'\bDrive\b', 'Dr', address)
		if re.search(r'\bGARDEN\b', address):
			return re.sub(r'\bGARDEN\b', 'GDN', address)
		if re.search(r'\bGarden\b', address):
			return re.sub(r'\bGarden\b', 'Gdn', address)
		if re.search(r'\bHEIGHTS\b', address):
			return re.sub(r'\bHEIGHTS\b', 'HTS', address)
		if re.search(r'\bHeights\b', address):
			return re.sub(r'\bHeights\b', 'Hts', address)
		if re.search(r'\bHIGHWAY\b', address):
			return re.sub(r'\bHIGHWAY\b', 'HWY', address)
		if re.search(r'\bHighway\b', address):
			return re.sub(r'\bHighway\b', 'Hwy', address)
		if re.search(r'\bPARKWAY\b', address):
			return re.sub(r'\bPARKWAY\b', 'PKY', address)
		if re.search(r'\bParkway\b', address):
			return re.sub(r'\bParkway\b', 'Pky', address)
		if re.search(r'\bPLACE\b', address):
			return re.sub(r'\bPLACE\b', 'PL', address)
		if re.search(r'\bPlace\b', address):
			return re.sub(r'\bPlace\b', 'Pl', address)
		if re.search(r'\bROAD\b', address):
			return re.sub(r'\bROAD\b', 'RD', address)
		if re.search(r'\bRoad\b', address):
			return re.sub(r'\bRoad\b', 'Rd', address)
		if re.search(r'\bSQUARE\b', address):
			return re.sub(r'\bSQUARE\b', 'SQ', address)
		if re.search(r'\bSquare\b', address):
			return re.sub(r'\bSquare\b', 'Sq', address)
		if re.search(r'\bSTREET\b', address):
			return re.sub(r'\bSTREET\b', 'ST', address)
		if re.search(r'\bStreet\b', address):
			return re.sub(r'\bStreet\b', 'St', address)
		if re.search(r'\bTERRACE\b', address):
			return re.sub(r'\bTERRACE\b', 'TERR', address)
		if re.search(r'\bTerrace\b', address):
			return re.sub(r'\bTerrace\b', 'Terr', address)
		if re.search(r'\bEXPRESSWAY\b', address):
			return re.sub(r'\bEXPRESSWAY\b', 'EXWY', address)
		if re.search(r'\bExpressway\b', address):
			return re.sub(r'\bExpressway\b', 'Exwy', address)
		else:
			return address

	def expand_address_direction(self, address):
		if re.search(r'\bN\b', address):
			return re.sub(r'\bN\b', 'North', address)
		if re.search(r'\bS\b', address):
			return re.sub(r'\bS\b', 'South', address)
		if re.search(r'\bE\b', address):
			return re.sub(r'\bE\b', 'East', address)
		if re.search(r'\bW\b', address):
			return re.sub(r'\bW\b', 'West', address)
		else:	
			return address

	def contract_address_direction(self, address):
		if re.search(r'\bNorth\b', address):
			return re.sub(r'\bNorth\b', 'N', address)
		if re.search(r'\bSouth\b', address):
			return re.sub(r'\bSouth\b', 'S', address)
		if re.search(r'\bEast\b', address):
			return re.sub(r'\bEast\b', 'E', address)
		if re.search(r'\bWest\b', address):
			return re.sub(r'\bWest\b', 'W', address)
		else:
			return address

	def get_roll_number(self, address):
	# Accepts a Hamilton address object and returns the roll number.
		url = "http://oldproperty.hamilton.ca/property-inquiry_noborders/list.asp"
		addressString = address['street_name']+" "+address['street_type_short']
		if address.get('street_direction_short') is not None:
			addressString = addressString+" "+address['street_direction_short']
		requestData = {
				"stnum": address['street_number'],
				"address": addressString,
				"community": "all000999",
				"B1": "Search"
			}
		response = BeautifulSoup(http_client.post(url, requestData).text, "html.parser")
		if response.find("b", text = re.compile("Roll Number")):
			print("Found roll number for "+str(address)+"! \n")
			return response.find("b", text = re.compile("Roll Number")).parent.parent.next_sibling.next_sibling.contents[0].strip()
		else:
			print("Can't find roll number for "+str(address)+"! \n")
			return None

	def validate_roll_number(self, roll_number):
	# Accepts a Hamilton roll number and validates whether it exists.
		url = "http://oldproperty.hamilton.ca/property-inquiry_noborders/detail.asp?qryrollno=" + roll_number
		if self.fetch(url).find("p", {"class": "heads"}, text = re.compile('property detail')):
			# print("Validated roll number "+roll_number+"! \n")
			# print("Roll number "+roll_number+" validated!")
			return roll_number
		else:
			# print("Can't validate roll number "+roll_number+"! \n")
			return None

	def get_address(self, roll_number):
	# Accepts a Hamilton roll number and returns an address.
		url = "http://oldproperty.hamilton.ca/property-inquiry_noborders/detail.asp?qryrollno=" + roll_number
		address = {}
		if self.fetch(url).find("p", {"class": "heads"}, text = re.compile('property detail')):
			def cleanAddressString(addressString):
				addressString = re.sub("\xa0", "", addressString)
				addressString = re.sub("\r", "", addressString)
				addressString = re.sub("\n", "", addressString)
				addressString = re.sub("\t", "", addressString)
				addressString = re.sub("-", "", addressString)
				addressString = re.sub("/", "", addressString)
				addressString = re.sub(" A ", "", addressString)
				addressString = re.sub(" B ", "", addressString)
				addressString = re.sub(" C ", "", addressString)
				addressString = re.sub(" D ", "", addressString)
				addressString = re.sub(' +', " ", addressString)
				addressString = addressString.strip()
				return addressString
			strName = cleanAddressString(self.fetch(url).find("b", text = re.compile('Property Address')).parent.parent.next_sibling.next_sibling.contents[0]).split(" ")[1]
			listURL = "http://oldproperty.hamilton.ca/property-inquiry_noborders/list.asp"
			requestData = {"address": strName, "community": "all000999", "B1": "search"}
			response = BeautifulSoup(http_client.post(listURL, requestData).text, "html.parser")
			if response.find_all("p", string="Property List"):
			# 	# print("Found roll numbers for streets named "+str(strName)+"! \n")
				address['street_number'] = response.find("a", text = re.compile(roll_number)).parent.parent.find_all("td")[1].contents[0].strip()
				address['street_name'] = response.find("a", text = re.compile(roll_number)).parent.parent.find_all("td")[2].contents[0].strip().split(" ")[0]
				address['street_type_short'] = response.find("a", text = re.compile(roll_number)).parent.parent.find_all("td")[2].contents[0].strip().split(" ")[1]
				if len(response.find("a", text = re.compile(roll_number)).parent.parent.find_all("td")[2].contents[0].strip().split(" ")) > 2:
					address['street_direction_short'] = response.find("a", text = re.compile(roll_number)).parent.parent.find_all("td")[2].contents[0].strip().split(" ")[2]
				if response.find("a", text = re.compile(roll_number)).parent.parent.find_all("td")[3].contents:
					address['unit'] = response.find("a", text = re.compile(roll_number)).parent.parent.find_all("td")[3].contents[0].strip()
				if response.find("a", text = re.compile(roll_number)).parent.parent.find_all("td")[4].contents:
					address['city'] = response.find("a", text = re.compile(roll_number)).parent.parent.find_all("td")[4].contents[0].strip()
		# print("Address: "+str(address))
		return address

	def fetch(self, url):
	# GET a URL and return the result ready to parse using BeautifulSoup
		return(BeautifulSoup(http_client.get(url).text, "html.parser"))

	def get_location(self, address):
	# Accepts a Hamilton address object and returns long/lat in EPSG:4326 and EPSG:3857 coordinates.
	# Required input address attributes:
	# 	'street_number'
	# 	'street_name'
	# 	'street_type_long'
	# 	'street_direction_short' or 'street_direction_long' if applicable
		url = "https://spatialsolutions.hamilton.ca/webgis/rest/services/Geocoders/Address_Locator/GeocodeServer/findAddressCandidates"
		addressString = address['street_number']+" "+address['street_name']+" "+address['street_type_long']	
		if address.get('street_direction_long') is not None:
			addressString = addressString+" "+address['street_direction_long']
		if address.get('city') is not None:
			addressString = addressString+" "+address['city']
		location = {}
		requestData4326 = {'SingleLine': addressString, 'f': 'json', 'outSR': '{wkid: 4326}', 'outFields': '*', 'maxLocations': '1'}
		response4326 = http_client.get(url, params=requestData4326).json()
		requestData3857 = {'SingleLine': addressString, 'f': 'json', 'outSR': '{wkid: 3857}', 'outFields': '*', 'maxLocations': '1'}
		response3857 = http_client.get(url, params=requestData3857).json()
		if response4326["candidates"]:
			location['EPSG:4326'] = response4326["candidates"][0]["location"]
			location['EPSG:3857'] = response3857["candidates"][0]["location"]
			# print("Found location for "+str(address)+"! \n")
		# else:
		# 	print("Can't find location for "+str(address)+"! \n")
		# print("Location: "+str(location))
		return location

	def get_ward(self, location):
	# Accepts a Hamilton location object and returns the city ward.
		if location:
			url = "https://spatialsolutions.hamilton.ca/webgis/rest/services/General/Political/MapServer/15/query"
			requestData = {
					'f': 'json',
					'outSR': '{wkid:4326}',
					'geometryType': 'esriGeometryPoint',
					'inSR': '{wkid:4326}',
					'geometry': "{'x': "+str(location['EPSG:4326']['x'])+", 'y': "+str(location['EPSG:4326']['y'])+", 'spatialReference': '{'wkid': '4326'}'}",
					'returnIdsOnly': 'true'
				}
			response = http_client.get(url, params=requestData)
			if response.json()['objectIds'] != None:
				# print("Ward: "+str(response.json()['objectIds'][0]))
				return str(response.json()['objectIds'][0])
			else:
				# print("Can't find ward for "+str(location))
				return None
		# else:
			# print("Can't get ward for empty location!")

	def get_tax_assessment_years(self, roll_number):
	# Accepts a roll number and returns a list of tax assessment years
		assessment_years = []
		url = "http://oldproperty.hamilton.ca/property-inquiry_noborders/detail.asp?qryrollno=" + roll_number
		for row in self.fetch(url).find("b", text = re.compile(r"Current Year Assessment")).parent.parent.parent.parent.find_all("tr"):
			if not (row.find(text = re.compile("Year")) or row.find(text = re.compile("Total Assessment")) or row.find(text = re.compile("Current Year Assessment"))):
				assessment_year = {}
				assessment_year["year"] = row.find_all("td")[0].contents[0].strip()
				assessment_year["class"] = row.find_all("td")[1].contents[0].strip()
				assessment_year["description"] = row.find_all("td")[2].contents[0].strip()
				assessment_year["amount"] = row.find_all("td")[3].contents[0].strip().replace(",", "")
				assessment_years.append(assessment_year)
		# print("Tax assessment years: "+str(assessment_years))
		return assessment_years

	def get_tax_levy_years(self, roll_number):
	# Accepts a roll number and returns a list of tax levy years
		tax_levy_years = []
		if not self.checkTaxExempt(roll_number):
			url = "http://oldproperty.hamilton.ca/property-inquiry_noborders/detail.asp?qryrollno=" + roll_number
			for row in self.fetch(url).find(text = re.compile("Tax Levy History")).parent.parent.parent.parent.parent.find_all("tr"):
				if not (row.find(text = re.compile("Tax Levy History")) or row.find(text = re.compile("Year"))):
					tax_levy_year = {}
					tax_levy_year["year"] = row.find_all("td")[1].contents[0].strip()
					tax_levy_year["amount"] = row.find_all("td")[2].contents[0].strip().replace(",", "")
					tax_levy_years.append(tax_levy_year)
		# print("Tax levy years: "+str(tax_levy_years))
		return tax_levy_years

	def get_tax_breakdown_years(self, roll_number):
	# Accepts a roll number and returns a list of tax breakdown years
		taxBreakDownYears = []
		if not self.checkTaxExempt(roll_number):
			url = "http://oldproperty.hamilton.ca/property-inquiry_noborders/detail.asp?qryrollno=" + roll_number
			for row in self.fetch(url).find(text = re.compile("Breakdown")).parent.parent.parent.parent.parent.find_all("tr"):
				if not (row.find(text = re.compile("Breakdown")) or row.find(text = re.compile("Type")) or row.find(text = re.compile("Total"))):
					taxBreakDownYear = {}
					taxBreakDownYear["year"] = self.fetch(url).find(text = re.compile("Breakdown")).split()[0]
					taxBreakDownYear[row.find_all("td")[0].contents[0].strip()] = row.find_all("td")[1].contents[0].strip().replace(",", "")	
					taxBreakDownYears.append(taxBreakDownYear)
		# print("Tax breakdown years: "+str(taxBreakDownYears))
		return taxBreakDownYears

	def get_tax_installment_years(self, roll_number):
	# Accepts a roll number and returns a list of tax installment years
		taxInstallmentYears = []
		if not self.checkTaxExempt(roll_number):
			url = "http://oldproperty.hamilton.ca/property-inquiry_noborders/detail.asp?qryrollno=" + roll_number
			for row in self.fetch(url).find_all(text = re.compile("Instalments"))[0].parent.parent.parent.parent.parent.find_all("tr"):
				if not (row.find(text = re.compile("Instalments")) or row.find(text = re.compile("Amount")) or row.find(text = re.compile("Total"))):
					taxInstallmentYear = {}
					taxInstallmentYear["year"] = self.fetch(url).find(text = re.compile("Instalments")).split()[0]
					taxInstallmentYear[arrow.get(row.find_all("td")[1].contents[0].strip(), 'MMMM\xa0D,\xa0YYYY').format('MM/DD/YYYY')] = row.find_all("td")[2].contents[0].strip().replace(",", "")
					taxInstallmentYears.append(taxInstallmentYear)
		# print("Tax installment years: "+str(taxInstallmentYears))
		return taxInstallmentYears

	def get_zoning_data(self, location):
	# Accepts a Hamilton location object and returns zoning data
		if location:
			url = "https://spatialsolutions.hamilton.ca/webgis/rest/services/General/Zoning/MapServer/dynamicLayer/query"
			response = {}
			checkRequestData = {
					'f': 'json',
					'outSR': '{wkid:4326}',
					'geometryType': 'esriGeometryPoint',
					'inSR': '{wkid:4326}',
					'geometry': "{'x': "+str(location['EPSG:4326']['x'])+", 'y': "+str(location['EPSG:4326']['y'])+", 'spatialReference': '{'wkid': '4326'}'}",
					'returnIdsOnly': 'true',
					'layer': "{'source':{'type':'mapLayer','mapLayerId': '9'}}"
				}
			checkResponse = http_client.get(url, params=checkRequestData).json()
			if checkResponse['objectIds'] != None:
				# print("Found zoning data for "+str(location)+"! \n")
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
				response = http_client.get(url, params=requestData).json()['features'][0]['attributes']
			# else:
			# 	print("Can't find zoning data for "+str(location)+"! \n")
			# print("Zoning: "+str(response))
			return response
		# else:
			# print("Can't get zoning data for empty location!")

	def get_temp_use_data(self, location):
	# Accepts a Hamilton location object and returns any temporary use applications
		if location:
			url = "https://spatialsolutions.hamilton.ca/webgis/rest/services/General/Zoning/MapServer/dynamicLayer/query"
			response = {}
			checkRequestData = {
					'f': 'json',
					'outSR': '{wkid:4326}',
					'geometryType': 'esriGeometryPoint',
					'inSR': '{wkid:4326}',
					'geometry': "{'x': "+str(location['EPSG:4326']['x'])+", 'y': "+str(location['EPSG:4326']['y'])+", 'spatialReference': '{'wkid': '4326'}'}",
					'returnIdsOnly': 'true',
					'layer': "{'source':{'type':'mapLayer','mapLayerId': '20'}}"
				}
			checkResponse = http_client.get(url, params=checkRequestData).json()
			if checkResponse['objectIds'] != None:
				# print("Found temporary use data for "+str(location)+"! \n")
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
				response = http_client.get(url, params=requestData).json()['features'][0]['attributes']
			# else:
			# 	print("Can't find temporary use data for "+str(location)+"! \n")
			# print("Temporary use: "+str(response))
			return response
		# else:
			# print("Can't get temporary use data for empty location!")

	def get_building_permit_apps(self, address):
	# Accepts a Hamilton address object and returns a list of any building permit applications
		applications = []
		cookieURL = "https://eplans.hamilton.ca/EPlansPortal/sfjsp?interviewID=Welcome"
		cookie = http_client.get(cookieURL, verify=False).headers['Set-Cookie'].split()[0][:-1]
		url = "https://eplans.hamilton.ca/EPlansPortal/sfjsp"
		headers = {"Cookie": cookie, "Host": "eplans.hamilton.ca"}
		response1Data = {"e_1482930323468": "onclick"}
		response1 = http_client.post(url, data = {"e_1482930323468": "onclick"}, headers = headers, verify = False)
		if address.get('street_direction_long') is not None:
			addressString = address['street_number']+';HAMILTON;'+address['street_name']+';'+address['street_direction_long']+';'
		else:
			addressString = address['street_number']+';HAMILTON;'+address['street_name']+';'
		response2Data = {
				"d_1536239857790": "buildingnewconstructionpermit",
				"d_1537469348077": "address",
				"d_1536259115820": addressString,
				"e_1536239857797": "onclick"
			}
		response2 = BeautifulSoup(http_client.post(url, data = response2Data, headers = headers, verify = False).text, "html.parser")
		if response2.find("div", {'class': 'panel-title'}):
			# print("Found building permit applications for "+str(address)+"! \n")		
			for row in response2.find("span", text = re.compile("Application #")).parent.parent.parent.parent.tbody.find_all("tr"):
				application = {}
				application["application_number"] = row.find_all("td")[0].div.contents[0].strip().replace(" ", "")
				application["description"] = row.find_all("td")[1].div.contents[0].strip()
				application["status"] = row.find_all("td")[3].div.contents[0].strip()
				applications.append(application)
		# else:
		# 	print("Can't find building permit applications for "+str(address)+"! \n")
		# print("Building permit applications: "+str(applications))
		return applications

	def checkTaxExempt(self, roll_number):
	# Returns true if the property associated with the roll number is tax exempt
		url = "http://oldproperty.hamilton.ca/property-inquiry_noborders/detail.asp?qryrollno=" + roll_number
		if self.fetch(url).find_all("td", {"class": "bodycopy"}, text = re.compile("Exempt")):
			# print(str(roll_number)+" is tax exempt! \n")
			return True
		# else:
		# 	print(str(roll_number)+" is NOT tax exempt! \n")