import pandas as pd

class Cooking:
    '''
    Container for cooking method and equipment fractions, mappings, and methods
    '''

    def __init__(self):
        # Map long cooking device name to short name
        device_lst = [['conveyorized char-broilers','ccb'],['underfired char-broilers','ucb'],
          ['deep-fat fryers','dff'],['flat griddles','fg'],['clamshell griddles','cg']]
        self.devices = pd.DataFrame(device_lst, columns=['cooking_device','device'])
        # Device fraction from table 2 of NEMO
        # SIC type, conv char-broiler %, underfire char-broiler %, deep-fat fryer %, flat griddle %, clamshell griddle %
        device_frac_lst = [['ethnic',0.035,0.475,0.819,0.627,0.040],
          ['fast_food',0.186,0.308,0.968,0.519,0.147],
          ['family',0.101,0.609,0.914,0.829,0.014],
          ['seafood',0.0,0.526,1.00,0.368,0.105],
          ['steak_bbq',0.069,0.552,0.828,0.897,0.0]]
        cols = ['sic_cuisine','ccb_frac','ucb_frac','dff_frac','fg_frac','cg_frac']
        self.device_frac = pd.DataFrame(device_frac_lst, columns=cols)
        # Device numbers from table 3 of NEMO
        # SIC type, conv char-broiler #, underfire char-broiler #, deep-fat fryer #, flat griddle #, clamshell griddle #
        device_tons_lst = [['ethnic',1.62,1.54,1.63,1.88,1.8],
          ['fast_food',1.07,1.58,3.10,1.43,2.09],
          ['family',1.71,1.29,2.34,2.03,0],
          ['seafood',0,1.10,2.47,1.11,1.50],
          ['steak_bbq',0,1.63,2.42,1.35,0]]
        cols = ['sic_cuisine','ccb_num','ucb_num','dff_num','fg_num','cg_num']
        self.device_num = pd.DataFrame(device_tons_lst, columns=cols)
        # Avg meat cook per year by device (tons) from table 4 of NEMO
        # meat type, conv char-broiler tons, underfire char-broiler tons, deep-fat fryer tons, flat griddle tons, clamshell griddle tons
        meats = [['steak',6.1,4.7,4.7,4.3,2.4],['hamburger',20.7,7.0,7.1,9.4,34.2],
          ['poultry',10.7,8.4,14.9,5.2,5.7],['pork',1.5,3.8,1.5,2.9,3.1],
          ['seafood',3.1,3.7,4.1,2.4,16.4],['other',0,1.1,7.1,1.5,0]]
        cols = ['food','ccb_tpy','ucb_tpy','dff_tpy','fg_tpy','cg_tpy']
        self.meat_tpy = pd.DataFrame(meats, columns=cols)
        # Scale factors for commercial/retail meat consumption based on USDA food consumption data (table 23.7 of 2023NEI TSD)
        comm_meat_scalars = [['steak', 0.2],['hamburger', 0.09],['poultry', 0.3],
          ['pork', 0.74],['seafood', 0.08],['other', 0.01]]
        self.cms = pd.DataFrame(comm_meat_scalars, columns=['food','scalar'])
        # Annual frozen potatoes used in food service (tons): 2988500 for 2020 NEI
        self.potato = 2988500
        # Fraction of these potatoes served at limited service (fast food) restaurants
        self.ff_potato_frac = 0.74
        # Approximately 700k restaurants in 2023 per BLS: https://www.bls.gov/iag/tgs/iag722.htm
        # Around 1M before 2020 https://www.foodindustry.com/answers/how-many-restaurants-are-there-in-the-united-states/
        self.national_restaurants = 700000
        # Number of limited service restaurants: https://www.ers.usda.gov/amber-waves/2023/june/limited-service-restaurants-closing-gap-with-full-service-establishments-in-rural-united-states/
        self.ff_fraction = 0.36

    def get_meat_tons(self):
        '''
        Set the tons of meat per cuisine by device
        '''
        df = pd.merge(self.device_frac, self.device_num, on='sic_cuisine', how='inner')
        devs = list(self.devices.device.drop_duplicates())
        for dev in devs:
            df[dev] = df[f'{dev}_frac'] * df[f'{dev}_num']
        df = pd.melt(df[['sic_cuisine',]+devs], id_vars='sic_cuisine', 
          var_name='device', value_name='dev_cnt')
        tons = pd.melt(self.meat_tpy, id_vars='food', var_name='device', value_name='meat_tons')
        tons.device = tons.device.str.split('_').str[0]
        df = df.merge(tons, on='device', how='left')
        df = df.merge(self.cms, on='food', how='left')
        df['food_tpy'] = df.dev_cnt.fillna(0) * df.meat_tons.fillna(0) * df.scalar.fillna(1)
        return df[['sic_cuisine','device','food','food_tpy']].copy()

    def calc_potato(self, df):
        '''
        Calc the potato tons per restaurant per county by cuisine
        '''
        # Fast food is simply the national tons of potato for fast food divided by the national fast food restaurans
        ff_tons = self.potato * self.ff_potato_frac / (self.national_restaurants * self.ff_fraction)
        # Full service is everything else
        fs_tons = self.potato * (1 - self.ff_potato_frac) / (self.national_restaurants * (1 - self.ff_fraction))
        # Only restaurants with deep fat fryers
        dff = df[(df.device == 'dff')].copy()
        dff['food'] = 'potatoes'
        dff.drop_duplicates(inplace=True)
        dff['food_tpy'] = fs_tons
        dff.loc[dff.sic_cuisine == 'fast_food', 'food_tpy'] = ff_tons
        return dff

