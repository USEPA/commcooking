import pandas as pd

class Cuisine:
    '''
    Container for cuisine-related mappings and functions
    '''

    def __init__(self, gapfiller='family'):
        # Steak and BBQ
        self.steak_bbq = ['steak','steak_house','bbq','barbeque','barbecue']
        # Seafood
        self.seafood = ['seafood','fish','lobster','crab','fish_and_chips','surf_and_turf','surf_&_turf','surf&turf','oyster','oysters']
        # A non-exhaustive list of "family" food types -- mostly American
        self.family = ['american','regional','burger','chicken','fusion','southwest','southwestern','new_american','breakfast',
          'gastropub','hot_dog','fried_chicken','farm-to-table','diner','soul_food','tex-mex','grill','wings','key_west','hawaiian',
          'regional','southern','bar&grill','californian','cafeteria','small_plates','cafe','deli','fries','poutine','bistro',
          'sausage','sandwich','pub']
        # A non-exhaustive list of "ethnic" food types
        self.ethnic = ['middle_eastern','chinese','italian','mexican','mediterranean','colombian','latin_american','thai','persian',
          'salvadoran','hot_pot','caribbean','french','asian_fusion','mongolian','mongolian_grill','polish','peruvian',
          'indian','greek','cuban','tapas','ethiopian','korean','german','russian','japanese','spanish','filipino',
          'jamaican','korean','vietnamese','dumplings','nigerian','brasserie','curry','kabob','asian','international','taco',
          'english','brazilian','cajun','sicilian','tibetan','pasta','taqueria','swiss','australian','argentine','ramen','tacos',
          'hibachi','puerto_rican','taiwanese','gyros','dumpling','afghan','african','burrito','kebab','hispanic','latin',
          'european','pupusa','irish','lebanese','turkish']
        # Certain restaurants don't put any cooked meat or potatoes on the menu
        # This set includes cuisine that is baked (pizza, bakery, etc.), served raw (sushi, salad, etc.), desserts, and others
        self.other = ['pizza','noodle','pancake','donut','coffee','bagel','sushi','salad','juice','dessert','pie','icecream',
         'ice_cream','bakery','poke','shaved_ice','cookie','tea','frozen_yogurt','smoothie','bubble_tea','soup','pretzel','coffee_shop',
         'snack','wine','crepe','grocery','slushy','slushie','calzone','yogurt','snowballs','fondue','pho','gelato','cocktails',
         'cake','wine']
        ## SIC mapping
        sic = [['ethnic','581201'],['fast_food','581203'],['family','581205'],['seafood','581207'],['steak_bbq','581208']]
        self.sic_codes = pd.DataFrame(sic, columns=['sic_cuisine','sic'])
        # Gapfill cuisine
        self.gapfiller = gapfiller

    def fill_primary_cuisine(self, food):
        '''
        Gapfill primary cuisine
        If a cuisine was not provided in OSM search on the restaurant name for common terms that indicate a cuisine
        The cuisine_map is given as a key: item pairing of name search term: cuisine type
        These should be clear unambiguous indicators of cuisine served or restaurant type.
        '''
        # First try to fill from the various food types as an ordered list
        for pc in self.steak_bbq+self.ethnic+self.seafood+self.family+self.other:
            idx = (food.primary_cuisine.isnull()) & (food['name'].str.lower().str.contains(pc.lower())) 
            food.loc[idx, 'primary_cuisine'] = pc.lower()
            food.loc[idx, 'comment'] = f'filled from name: {pc.lower()}'
        # Then map in
        cuisine_map = {'grill': 'burger', 'burrito': 'mexican', 'mexico': 'mexican', 'hoagie': 'sandwich', 
          'china': 'chinese', 'india': 'indian', 'italy': 'italian', 'pizzeria': 'pizza'}
        for ns, pc in cuisine_map.items():
            idx = (food.primary_cuisine.isnull()) & (food['name'].str.lower().str.contains(ns.lower()))
            food.loc[idx, 'primary_cuisine'] = pc.lower()
            food.loc[idx, 'comment'] = f'filled from name: {ns.lower()}'
        return food

    def assign_sic_cuisine(self, food):
        '''
        Assign the SIC cuisine type based on the primary cuisine
        The primary map contains a pairing of SIC cuisine: [primary, cuisine, in, SIC...]
        A few overrides are provided based on amenity type and secondary cuisine (if available)
        '''
        primary_map = {'steak_bbq': self.steak_bbq, 'family': self.family, 'ethnic': self.ethnic,
          'seafood': self.seafood}
        # This is not an exhaustive mapping...
        food['sic_cuisine'] = ''
        # Set based on a primary cuisine mapping
        for sic_cuisine, primary_cuisine in primary_map.items():
            food.loc[food.primary_cuisine.isin(primary_cuisine), 'sic_cuisine'] = sic_cuisine
        # Gapfill based on secondary cuisine
        # This covers places like Dairy Queen where the first cuisine is ice cream but the second is hamburgers
        for sic_cuisine, primary_cuisine in primary_map.items():
            food.loc[(food.secondary_cuisine.isin(primary_cuisine)) & (food.sic_cuisine == ''), 'sic_cuisine'] = sic_cuisine
        # Fast food override for restaurants in the fast food amenity type
        # We don't want all fast food to be set to fast food because there are a lot of places like Dunkin Donuts that shouldn't have emissions
        idx = ((~ food.primary_cuisine.isin(self.other)) | (food.sic_cuisine == '')) & (food.amenity == 'fast_food')
        food.loc[idx, 'sic_cuisine'] = 'fast_food'
        # Pubs are assumed to serve generic American "family" fare
        food.loc[(food.sic_cuisine == '') & (food.amenity == 'pub'), 'sic_cuisine'] = 'family'
        # Assign restaurants that don't cook meat or fries to "noemit"
        food.loc[(food.primary_cuisine.isin(self.other)) & (food.secondary_cuisine.fillna('coffee').isin(self.other)), 'sic_cuisine'] = 'noemit'
        return food

    def gapfill_cuisine(self, food):
        '''
        Gapfill any cuisine without an SIC to the gapfiller
        '''
        # Gapfill everything else with a specified type
        idx = (food.sic_cuisine == '')
        food.loc[idx, 'comment'] = f'; gapfilled with {self.gapfiller}'
        food.loc[idx, 'sic_cuisine'] = self.gapfiller
        return food

