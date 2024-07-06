from utils_04Jul2024 import House, Household, HousingMarket
import pandas as pd
import numpy as np 

np.random.seed(0)

# 30Jun2024: We're effectively running five distinct simulations, with the ultimate aim of evaluating the impact of different average house
# prices on results. Note that the loop begins at 0, NOT 1, meaning we have to add 1 to each integer.
for j in range(5):
    agent_income_avg = 20000
    agent_income_std = 2050
    agent_wealth_avg = 1000000
    agent_wealth_std = 500000
    h_price_avg = (j + 1)*1000000
    h_price_std = 250
    h_rent_avg = 1000
    h_rent_std = 250
    
    # # Add houses to the housing_stock list
    housing_stock = []
    # 30Jun2024: There may be a way to streamline this, but for the moment housing_stock (presumably used in calculations) and house_data
    # (used for reporting) are generated in parallel. The reason for this is that house_data appears to use a subset of the available data
    # that is then converted into a dataframe (which cannot be accomplished in a straighforward fashion with housing_stock).
    house_data = []
    for i in range(200):
        # Add housing stats here
        house = House(h_price_avg, h_price_std, h_rent_avg, h_rent_std)
        housing_stock.append(house)
        house_data.append({'ID': house.id, 'Price': house.price, 'Rent': house.rent})

    house_data = pd.DataFrame(house_data)
    
    # Add agent wealth variables here
    model = HousingMarket(200, agent_income_avg, agent_income_std, agent_wealth_avg, agent_wealth_std, housing_stock)
    for i in range(30):
        model.step()
    
    agent_data = model.datacollector.get_agent_vars_dataframe().reset_index()
    
    # Group by 'Step' and 'AgentType' and count occurrences
    summary_stats = agent_data.groupby(['Step', 'AgentType', 'Ethnicity']).size().reset_index(name='Count')
    summary_stats.to_csv('summary_stats_' + str(j + 1) + '.csv', index=False)

    # 30Jun2024: Attempting to output wealth data collected by the model.
    wlth_rpt = agent_data.groupby(['Step', 'AgentType']).agg({'Wealth': 'mean', 'NumHouses': 'mean'}).reset_index()
    wlth_rpt['Wealth'] = wlth_rpt['Wealth'].round(2)
    wlth_rpt['NumHouses'] = wlth_rpt['NumHouses'].round(2)
    wlth_rpt.to_csv('wlth_rpt' + str(j + 1) + '.csv', index=False)

    # 30Jun2024: Output initial house prices and rent. This is useful at the outset to get a sense of the initial range of, and variability in prices.
    house_data.to_csv('hs_data' + str(j + 1) + '.csv', index=False)
    
    # Pivot the DataFrame to get 'AgentType' as columns
    pivot_table = summary_stats.pivot_table(index='Step', columns='AgentType', values='Count', fill_value=0)
    pivot_table.to_excel('pivot_table_' + str(j + 1) + '.xlsx', index=True)