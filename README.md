# Local Soup Hamilton

## What is this?

This is a Python class that scours the internet for available data about a specific property in Hamilton Ontario, and assembles them into a nice, clean, thoughtfully constructed [JSON](https://www.w3schools.com/whatis/whatis_json.asp) record. You can run it locally to get information about a particular address you're interested in. Or you could use it as a building block to aggregate Hamilton property data into a big juicy database.

## How to use it

### Install the dependencies

Here's what you need to download and install:
- [Git](https://git-scm.com/downloads)
- [Python](https://www.python.org/downloads/)

And here are the Python packages you need to install using [pip](https://www.w3schools.com/python/python_pip.asp):
- requests
- http
- bs4
- re
- arrow
- logger
- http_client

#### Clone the files...

...by running this command:

``git clone https://github.com/localsoup/hamilton``

(Or you can just download them into a local directory from GitHub.)

You'll need them all. Here's what they do.

- **ls_hamilton_property_class.py:** This is the file that contains the class, which is called ls_hamilton_property. When you instantiate the class you pass it an address object, and it uses the address to build out a fuller property record that includes tax information, zoning data, building permits, etc. 

- **ls_hamilton_property_test.py:** This is the file you actually run. It contains a few sample addresses, including a fake one - comment all of them out except the one you want to try. It invokes the class, creates a property record with the provided address, and prints the record to your console. 

- **logger.py:** Sets up logging for the class. You don't need to touch this file unless you want to change the level of logging - the default is 10, which is Debug mode. Everything is logged as JSON records to a local file called localsoup.log. 

- **http_client.py:** Sets up the HTTP client for the class. You don't need to touch this file unless you want to adjust the default timeout, the level of HTTP logging to your console (the default is none, it's all going into the log file), and the retry strategy. 

### Run the test file

The ls_hamilton_property_test.py file contains a bunch of sample address records that look like this:

``my_address = {'street_number': '73', 'street_name': 'Tisdale', 'street_type_short': 'ST', 'street_direction_short': 'S', 'city': 'Hamilton'}``

You can add your own addresses to try them out. Comment out all the address except the one you want to run by adding a # character at the front of the line. Then run the file from the command line

``python ls_hamilton_property_test.py``

The code will print a JSON record to your console screen - it might take a few seconds, because there's a lot of data to assemble from a lot of different places. If it's unsuccessful, it will just print a record that's empty except for the original address you provided. You can look in the localsoup.log file to see what happened. Sometimes the applications and services that provide the data go down and aren't available, and sometimes the address just doesn't match. But if it works, it'll be full of good stuff.


## The address object
The ls_hamilton_property class accepts an address object and returns a property object that includes all of the information it has found. The class has it's own naming conventions for address attributes, so you'll need to format your address accordingly before submitting it. Here are all the address attributes. For clarity, I'll use this address for examples: 

73 Tisdale Street South, Hamilton, Ontario, Canada, L8N 2W1

| Attribute | Description | Required? |
| --------- | ----------- | --------- |
| street_number | E.g. 73 | Yes |
| street_name | E.g. Tisdale | Yes |
| street_type_long | The full name of the type of street, e.g. Street. Also accepts Avenue, Boulevard, Circle, Court, Crescent, Drive, Garden, Heights, Highway, Parkway, Place, Road, Square, Terrace, Expressway, Village, Point and Sideroad | Yes. However, you must specify either a long or short street type. You don't need to specify both. |
| street_type_short | The abbreviated name of the type of street, e.g. St. Also accepts Ave, Blvd, Cir, Crt, Cres, Dr, Gdn, Hts, Hwy, Pky, Pl, Rd, Sq, Terr, Exwy, Villge, Pt and Siderd. | Yes. However, you must specify either a long or short street type. You don't need to specify both. |
| street_direction_long | E.g. South. Also accepts North, East and West. | No. Also, you only need to specify either a long or short street type. You don't need to specify both. |
| street_direction_short | E.g. S. Also accepts N, E and W. | No. Also, you only need to specify either a long or short street type. You don't need to specify both. |
| city | E.g. Hamilton. Also accepts Ancaster, Dundas, Flamborough, Glanbrook and Stoney Creek. | Yes |


## The property object

The ls_hamilton_property class returns a property object. Here's an example:

```
{
    "address": {
        "street_number": "17",
        "street_name": "Discovery",
        "street_type_short": "DR",
        "city": "Hamilton",
        "street_type_long": "DRIVE",
        "validated": "True",
        "neighborhood": ""
    },
    "location": {
        "EPSG:4326": {
            "x": -79.86064186418574,
            "y": 43.274923539312546
        },
        "EPSG:3857": {
            "x": -8890045.986745141,
            "y": 5353912.075112301
        }
    },
    "taxes": [
        {
            "roll_number": "02016408140",
            "is_tax_exempt": true,
            "assessment_years": [
                {
                    "year": "2022",
                    "class": "E",
                    "description": "Exempt",
                    "amount": "1653600"
                }
            ]
        },
        {
            "roll_number": "02016499999",
            "is_tax_exempt": false,
            "assessment_years": [
                {
                    "year": "2022",
                    "class": "CT",
                    "description": "Commercial Taxable",
                    "amount": "637400"
                }
            ],
            "levy_years": [
                {
                    "year": "2022",
                    "amount": {
                        "total": "19393.86",
                        "municipal_levy": "13784.74",
                        "education_levy": "5609.12"
                    },
                    "installments": [
                        {
                            "date": "02/28/2022",
                            "amount": "4733.00"
                        },
                        {
                            "date": "04/29/2022",
                            "amount": "4732.46"
                        },
                        {
                            "date": "06/30/2022",
                            "amount": "4964.00"
                        },
                        {
                            "date": "09/30/2022",
                            "amount": "4964.40"
                        }
                    ]
                },
                {
                    "year": "2021",
                    "amount": {
                        "total": "18930.92"
                    }
                }
            ]
        }
    ],
    "ward": "2",
    "zoning": {
        "ZONING_CODE": "F-1/S-1641-H",
        "ZONING_DESC": "Waterfront Recreational - Holding",
        "PARENT_BY_LAW_NUMBER": "6593 Former Hamilton",
        "PARENT_BY_LAW_URL": "https://www.hamilton.ca/city-planning/official-plan-zoning-by-law/zoning-by-laws-former-communities",
        "BY_LAW_NUMBER": "14-042",
        "BY_LAW_URL": "https://www.hamilton.ca/government-information/by-laws-and-enforcement/by-laws-passed-in-2014",
        "EXCEPTION1": null,
        "EXCEPTION1_BYLAW": null,
        "EXCEPTION1_URL": null,
        "HOLDING1": null,
        "HOLDING1_BYLAW": null,
        "HOLDING1_URL": null,
        "HOLDING2": null,
        "HOLDING2_BYLAW": null,
        "HOLDING2_URL": null,
        "HOLDING3": null,
        "HOLDING3_BYLAW": null,
        "HOLDING3_URL": null,
        "COMMUNITY": "Hamilton",
        "ZONING_MAP": "827",
        "COUNCIL_APP_DATE": 1393390800000,
        "ZONING_FILE": "CI-13-A",
        "OMB_NUMBER": "PL140315",
        "OMB_CASE_NUMBER": "PL140314",
        "OPA_NUMBER": null,
        "URBAN_RURAL_SETTLE": "U",
        "FINALBINDING_DATE": 1575954000000,
        "SHAPE.AREA": 37789.36920364,
        "SHAPE.LEN": 1066.4679101219301
    },
    "temp_use": {},
    "building_permits": [
        {
            "application_number": "2019574500",
            "description": "To demolish a 2- storey, 258 m\u00b2 office building (former Hamilton Marine Police Unit).",
            "status": "Closed"
        }
    ]
}
```

## Data sources

All of the data that the class collects is freely available public data published by the City of Hamilton to the open internet for anybody to use in any way they see fit. It's just scattered about and hard to access. The class gets at the data either by parsing HTML from city-run Web applications (using a fantastic Python package called [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/), or by querying services that provide data for various maps that the city has published.

Here are the data sources:

### Address search

The City of Hamilton publishes an ArcGIS web endpoint for finding Hamilton addresses at: 

https://spatialsolutions.hamilton.ca/webgis/rest/services/Geocoders/Address_Locator/GeocodeServer/findAddressCandidates

The class uses this service to verify addresses, append additional data to them, and retrieve lat/long coordinates.

### Ward boundaries

The City of Hamilton publishes an ArcGIS web endpoint for retriving the ward of a given address at:

https://spatialsolutions.hamilton.ca/webgis/rest/services/General/Political/MapServer/15/query

The class uses this service to append the ward to the property record.


### Zoning search

The City of Hamilton publishes an ArcGIS web endpoint for retriving zoning data at:

https://spatialsolutions.hamilton.ca/webgis/rest/services/General/Zoning/MapServer/dynamicLayer/query

The class uses this service to append zoning classifications and temporary use exemptions to the property record.


### Building permits

The City of Hamilton hosts a JSP application for building permit searches at:

https://eplans.hamilton.ca/EPlansPortal/sfjsp

The class uses this application to retrieve and append building permit applications and statuses to the property record.


### Property taxes

The City of Hamilton hosts an ASP application for inquiring about property taxes at:

http://oldproperty.hamilton.ca/property-inquiry_noborders/default.asp

The class uses this application to retrieve and append roll numbers, tax assessments, and tax levies to the property record.


## License

This code is licensed under the [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0) open source license.
