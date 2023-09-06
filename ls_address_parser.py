class ls_hamilton_address:
    # def __init__(self, address={})
    def __init__(self, address):
        # self.address = {}
        # self.address["street_number"] = address["house_number"]
        self.street_number = address["house_number"]
        # self.address["street_name"] = self.parse_street(address["road"])["street_name"]
        self.street_name = self.parse_street(address["road"])["street_name"]
        # self.address["street_type_long"] = self.parse_street(address["road"])["street_type_long"]
        self.street_type_long = self.parse_street(address["road"])["street_type_long"]
        if "street_direction_long" in self.parse_street(address["road"]):
            # self.address["street_direction_long"] = self.parse_street(address["road"])["street_direction_long"]
            self.street_direction_long = self.parse_street(address["road"])["street_direction_long"]
        # self.address["city"] = address["city"]
        self.city = address["city"]
        self.postal = address["postcode"]

    def parse_street(self, road):
        road_list = list(road.split(" "))
        length = len(road_list)
        last_road_value = road_list[length-1]
        direction_list = ["North", "East", "South", "West"]
        try:
            direction_list.index(last_road_value)
            street_name_list = road_list[0:length-2]
            street_name = " "
            return {"street_name": street_name.join(street_name_list), "street_type_long": road_list[length-2], "street_direction_long": road_list[length-1]}
        except ValueError:
            street_name_list = road_list[0:length-1]
            street_name = " "
            return {"street_name": street_name.join(street_name_list), "street_type_long": road_list[length-1]}