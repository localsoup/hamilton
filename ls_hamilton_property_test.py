import ls_hamilton_property_class
import json


# my_address = {'street_number': '73', 'street_name': 'Tisdale', 'street_type_short': 'ST', 'street_direction_short': 'S', 'city': 'Hamilton'}
# my_address = {'street_number': '194', 'street_name': 'King', 'street_type_short': 'ST', 'street_direction_short': 'W', 'city': 'Hamilton'}
my_address = {'street_number': '17', 'street_name': 'Discovery', 'street_type_short': 'DR', 'city': 'Hamilton'}
# my_address = {'street_number': '123', 'street_name': 'Baloney', 'street_type_short': 'DR', 'city': 'Nowheresville'}


my_prop = ls_hamilton_property_class.ls_hamilton_property(address=my_address)
print(json.dumps(my_prop.__dict__, indent=4))


