import pyrosm as pyr
import pandas as pd

class Restaurants:

    def __init__(self):
        '''
        '''
        # Columns to include from the OSM data
        col_names = ['brand','operator','official_name','name']
        col_loc = ['addr:housenumber','addr:street','addr:city','addr:state',
          'addr:postcode','lon','lat','region_cd']
        col_cuisine = ['amenity','cuisine']
        col_meta = ['id','version','timestamp']
        self.osm_columns = col_names+col_loc+col_cuisine+col_meta
        # OSM POI Filter: set for restaurant, fast_food, and pub amenities
        # Filter syntax is available in the pyrosm documentation
        self.osm_filter = {'amenity': ['restaurant','fast_food','pub']}
        # Additional attributes to load for a POI
        self.extra_atts = ['brand','cuisine','official_name','addr:state'] 

    def read_osm(self, osm_pbf):
        '''
        Load and filter the OSM PBF
        '''       
        osm = pyr.OSM(osm_pbf)
        # Grab the amenities from the OSM file
        # Filter to just food -- what about Sheetz, WaWa, Bucees, etc?
        self.food = osm.get_pois(custom_filter=self.osm_filter, extra_attributes=self.extra_atts)
        print(f'Restaurants read: {len(self.food)}', flush=True)
        # Add in the centroid
        self._get_centroids() 

    def subset_columns(self):
        '''
        Subset to the OSM columns, removing geometry
        '''
        self.food = pd.DataFrame(self.food[self.osm_columns])

    def filter_restaurant_brands(self):
        '''
        Filter the output of certain types of food at specific restaurant brands
        According to the survey used in the NEMO, restaurants that did not cook meat were removed from the survey
        https://ww2.arb.ca.gov/sites/default/files/classic/research/apr/reports/l943.pdf
        Focus on the menus of the largest brands/chains
        This is only for the food types that use one of the estimated cooking methods. 
          ex. Selling pre-cooked chicken would not result in food emissions.
        '''
        brands = {'no_potatoes': ["Subway","Panera Bread","Jersey Mike's","Qdoba","Taco Bell","Panda Express","Jimmy John's","Chipotle"],
        # I'm considering any ground beef to be "hamburger"
        'no_hamburger': ["Chick-fil-A","Popeyes","KFC","Subway","Panera Bread","Jersey Mike's","Qdoba","Jimmy John's"],
        'no_poultry': ["Subway","Panera Bread","Jersey Mike's","Jimmy John's"],
        'no_steak': ["Subway","Panera Bread","Jimmy John's","Chick-fil-A","Popeyes","KFC"],
        'no_seafood': ["Chipotle","Subway","Panera Bread","Jersey Mike's","Qdoba","Taco Bell","Jimmy John's","Chick-fil-A","Popeyes","Taco Bell"],
        'no_pork': ["Chick-fil-A","Popeyes","KFC","Subway","Panera Bread","Jersey Mike's","Qdoba","Jimmy John's"],
        # Mutton? Pheasant?
        'no_other': ["Chipotle","Subway","Panera Bread","Jersey Mike's","Qdoba","Taco Bell","Jimmy John's","Chick-fil-A","Popeyes","Taco Bell","McDonald's","Burger King"]}
        for cuisine, brand_list in brands.items():
            self.food.loc[(self.food.brand.isin(brand_list)) & (self.food.food == '_'.join(cuisine.split('_')[1:])), 'food_tpy'] = 0

    def _get_centroids(self):
        '''
        Get the centroid of the shapes as the release point location
        '''
        self.food.geometry = self.food.geometry.to_crs(epsg=5070)
        self.food['centroid'] = self.food.geometry.centroid
        self.food.cent = self.food.centroid.to_crs(epsg=4326)
        self.food['lon'] = self.food.cent.x
        self.food['lat'] = self.food.cent.y

    def set_cuisine(self):
        '''
        Define the primary and secondary cuisine
        '''
        self.food['primary_cuisine'] = self.food.cuisine.str.split(';').str[0]
        self.food['secondary_cuisine'] = self.food.cuisine.str.split(';').str[1]


