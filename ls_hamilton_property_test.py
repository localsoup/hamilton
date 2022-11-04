import ls_hamilton_property_class
import json

my_address = {'street_number': '73', 'street_name': 'Tisdale', 'street_type_short': 'ST', 'street_direction_short': 'S'}

# my_address = {'street_number': '123', 'street_name': 'King', 'street_type_short': 'ST', 'street_direction_short': 'W'}


# my_address = {'street_number': '17', 'street_name': 'Discovery', 'street_type_short': 'DR'}

my_prop = ls_hamilton_property_class.ham_prop(address=my_address)

# my_roll_number = '03020406170'

# my_roll_number = '02016408140'

# my_prop = ls_hamilton_property_class.ham_prop(roll_number=my_roll_number)



print(json.dumps(my_prop.__dict__, indent=4))