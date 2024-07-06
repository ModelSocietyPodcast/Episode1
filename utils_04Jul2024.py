import mesa
import numpy as np
from mesa.datacollection import DataCollector
np.random.seed(0)

class HousingMarket(mesa.Model):
    """"Model with Household Agents"""
    def __init__(self, N, income_avg, income_std, wealth_avg, wealth_std, housing_stock):
        super().__init__()
        self.num_agents = N
        self.schedule = mesa.time.RandomActivation(self)
        self.income_avg = income_avg
        self.income_std = income_std
        self.wealth_avg = wealth_avg
        self.wealth_std = wealth_std
        self.housing_stock = housing_stock
        
        # Custom agent reporter function to calculate the length of the 'houses' attribute
        def count_houses(agent):
            return len(agent.houses)

        # Initialize DataCollector with the custom agent reporter
        # 30Jun2024: What's really going on here? You're recording the state of the simulation at any given time, but I don't have any recollection of this
        # being reported anywhere. Maybe the data is being collected but not output? In fact, removing wealth from the statement has no impact on the results.
        # I think it was intended this should be reported, but also that this did not happen. Let's see if we can operationalize.
        self.datacollector = DataCollector(agent_reporters={"Wealth": "wealth", "AgentType": "agent_type", "Ethnicity": "ethnicity", "NumHouses": count_houses})
            
        # Create agents
        for i in range(self.num_agents):
            a = Household(i, self, self.income_avg, self.income_std, self.wealth_avg, self.wealth_std, self.housing_stock)
            self.schedule.add(a)

    def step(self):
        # Call model and move it one period forward
        self.schedule.step()
        # Collect agent-level data at each step
        self.datacollector.collect(self)

class Household(mesa.Agent):
    """An agent with wealth, income and housing needs"""
    def __init__(self, unique_id, model, income_avg, income_std, wealth_avg, wealth_std, housing_stock):
        super().__init__(unique_id, model)
        self.wealth = max(0, np.random.normal(wealth_avg, wealth_std))
        # Only positive incomes
        # 04Jul2024: We assume there is a income floor that could be seen to reflect the presence of a social security net or minimum wage legislation.
        self.income = max(0.1*income_avg, np.random.normal(income_avg, income_std))
        self.agent_type = "displaced"
        if np.random.uniform(0, 1) > 0.5:
            self.ethnicity = "white"
        else:
            self.ethnicity = "black"
        self.houses = []
        self.rent_payment = None
        self.leased_house = None
        self.housing_stock = housing_stock 

    def buy_house(self):
        """Buy a house and add it to the list of owned houses"""
        for house in self.housing_stock:
            if self.ethnicity == "white":
                threshold = 1*self.wealth
            else:
                threshold = 0.75*self.wealth
            if house.status == "vacant" and house.price < threshold:
                house.status = "owned"
                house.owner = self.unique_id
                self.wealth -= house.price 
                self.houses.append(house.id)
                break

    def rent_out_house(self):
        """If you have multiple houses, rent them out"""
        for house in self.housing_stock:
            # Match additional house to housing stock
            if house.id == self.houses[-1]:
                house.status = "for_rent"

    def rent_house(self):
        """Rent a house"""
        for house in self.housing_stock:
            if house.status == "for_rent" and house.rent < 0.3*self.income:
                house.status = "rented"
                self.agent_type = "renter"
                self.rent_payment = house.rent
                self.leased_house = house.id
    
    def collect_rent(self):
        """If you have rented houses, collect the rent payment"""
        if self.agent_type == "investor":
            for house in self.housing_stock:
                if house.status == "rented" and house.id in self.houses:
                    self.wealth += house.rent

    def step(self):
        # print(f"ID#: {self.unique_id} is a {self.agent_type} with income: {self.income:2f} and wealth {self.wealth:2f}")
        # Generate income every year; this then is added to the household's wealth.
        self.wealth += self.income
        # income appears to increase at 5% every period.
        self.income = self.income*1.05
        
        # Determine agent type and course of action
        # 30Jun2024: This next piece effectively encompasses the decision rules that governs the agent's actions. Note the hierarchy:
        # 1. Check if they already own more than one house. If so, they're an investor, so run the rent_out_house algorithm.
        # 2. Check if they own exactly one house. If so, don't do anything (yet).
        # 3. Try to buy a house (buy_house algorithm). This seems to apply no matter what class the individual is. This is also not unproblematic, because
        # status is not re-evaluated after the purchase has been made. This means that in some periods, people may not be credited as investors/owners even
        # if they have in fact purchased a home. One way to potentially address this is to move the buy_house algorithm first.

        # Try to buy a house.
        # 30Jun2024: This previously came after the ownership check, but I observed that this led to some odd results when running summary statistics.
        self.buy_house()
        
        if len(self.houses) > 1:
            self.agent_type = "investor"
            # Rent house if you have multilple
            self.rent_out_house()

        if len(self.houses) == 1:
            self.agent_type = "owner"

        # If renting, remove rent from wealth
        if self.agent_type == "renter":
            self.wealth -= self.rent_payment
        
        # If too expensive, try to rent a house
        if self.agent_type == "displaced":
            self.rent_house()

class House():
    """"A class representing a house asset."""
    next_id = 1
    def __init__(self, h_price, h_price_std, h_rent, h_rent_std):
        # Assign the next available id to the current instance
        self.id = House.next_id
        # Increment the next available id for the next instance
        House.next_id += 1
        self.price = np.random.normal(h_price, h_price_std)
        # Quality is not currently used in the model - we can reintroduce this later.
        # self.quality = np.random.uniform(1, 10)
        self.rent = np.random.normal(h_rent, h_rent_std)
        self.owner = None
        self.status = "vacant"