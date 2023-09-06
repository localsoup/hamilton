import ls_address_parser
import ls_hamilton_property_class
import json



my_address = {
            "house_number": "73",
            "road": "Tisdale Street South",
            "city": "Hamilton",
            "county": "Golden Horseshoe",
            "state": "Ontario",
            "postcode": "L8N 2W1",
            "name": "Tisdale Street South",
            "country": "Canada",
            "country_code": "ca"
        }


# my_address = {
# 			"house_number": "17",
# 			"road": "Discovery Drive",
# 			"neighbourhood": "North End",
# 			"city": "Hamilton",
# 			"county": "Golden Horseshoe",
# 			"state": "Ontario",
# 			"postcode": "L8L 8K4",
# 			"name": "Discovery Drive",
# 			"country": "Canada",
# 			"country_code": "ca"
#         }

# my_address = {
#             "house_number": "689",
#             "road": "West 5th Street",
#             "city": "Hamilton",
#             "county": "Golden Horseshoe",
#             "state": "Ontario",
#             "postcode": "L9C 3R3",
#             "name": "West 5th Street",
#             "country": "Canada",
#             "country_code": "ca"
#         }


parsed_address = ls_address_parser.ls_hamilton_address(address=my_address)

# print(json.dumps(parsed_address.__dict__, indent=4))

# prop = ls_hamilton_property_class.ls_hamilton_property(address=parsed_address)

prop = ls_hamilton_property_class.ls_hamilton_property(address=parsed_address.__dict__)

print(json.dumps(prop.__dict__, indent=4))