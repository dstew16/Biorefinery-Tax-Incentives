# -*- coding: utf-8 -*-
"""
Created on Sun Oct  4 12:18:15 2020

@author: dalton w stewart
modified version of debug.py by yrc2

This file includes the tax incentives from incentives.py into a TEA. It does not include net metering programs.
"""
import os
import pandas as pd
import numpy as np
from biorefineries import lipidcane as lc
from incentives import TaxIncentives
import biosteam as bst


    
class IncentivesTEA(lc.ConventionalEthanolTEA):
    
    def __init__(self, *args, state='KY', with_federal_incentives=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = state
        self.with_federal_incentives = with_federal_incentives
        
    # bst.PowerUtility.price = .0671
    
    def _fill_incentives(self, incentives, taxable_cashflow, nontaxable_cashflow, tax):
        operating_hours = self._operating_hours
        ethanol = 0.
        for i in self.system.products:
            if 'Ethanol' in i.chemicals:
                F_mol = i.F_mol 
                if F_mol and i.imol['Ethanol'] / i.F_mol > 0.95:
                    ethanol = i.get_total_flow('gal/hr') * operating_hours
                    break
        biodiesel_eq = 0.
        for s in self.system.streams:
            if 'Lipid' in i.chemicals:
                F_mol = i.F_mol 
                if F_mol and i.imol['Lipid'] / i.F_mol > 0.95:
                    biodiesel_eq = sum([i.installed_cost for i in s.sink._downstream_units])
                    break
        ethanol_eq = 0.
        for sys in self.system.subsystems:
            if sys.ID == 'ethanol_production_sys':
                ethanol_eq = sum([i.installed_cost for i in sys.units])
        elec_eq = sum([i.installed_cost for i in self.units if i.power_utility.production])
        TCI = self.TCI
        self.tax_incentives = tax_incentives = TaxIncentives(
             state=self.state,
             plant_years=self._years + self._start, 
             variable_incentive_frac_at_startup=self.startup_VOCfrac,
             wages=self.labor_cost, 
             TCI=TCI, 
             ethanol=ethanol,
             state_income_tax=500000, # TODO: Verify this assumption
             jobs_50=50, # TODO: This is not explicit in BioSTEAM 
             elec_eq=elec_eq,
             construction_costs=TCI, # TODO: Verify this assumption 
             subcontract_fees=50000, # TODO: Verify this assumption
             racks_etc=25000, # TODO: Verify or find a way to estimate
             NM_value=1e6, # TODO: What is this?
             adj_basis=TCI, # TODO: Verify this assumption
             value_add=TCI, # TODO: Verify this assumption
             state_property_tax=200000, # TODO: Verify this assumption
             airq_taxes=100000, # TODO: Verify this assumption
             fuel_mix_eq=0., # TODO: This can be ignored 
             biodiesel_eq=biodiesel_eq, 
             ethanol_eq=ethanol_eq,
             elec_use=sum([i.power_utility.consumption for i in self.units]),
             elec_gen=sum([i.power_utility.production for i in self.units]),
             op_hours=operating_hours,
             start=self._start)
        credits_ = tax_incentives.calc_all_tax_incentives(df=False, include_federal=self.with_federal_incentives)    
        credits_[credits_ > tax] = tax
        incentives[:] = credits_
        
tea = lc.create_tea(lc.lipidcane_sys, IncentivesTEA)

folder = os.path.dirname(__file__)
available_states = ('AK','AL','AR','AZ','CA','CO','CT','DE','FL','GA','HI','IA','ID','IL','IN','KS','KY','LA'
                     ,'MA','MD','ME','MI','MN','MO','MS','MT','NC','ND','NE','NH','NJ','NM','NV','NY','OH','OK',
                     'OR','PA','RI','SC','SD','TN','TX','UT','VA','VT','WA','WI','WV','WY')

prices_by_state_with_federal = {}
prices_by_state_without_federal = {}


for state in available_states:
            # bst.PowerUtility.price = .06#nm_data.loc['rate',state]
            # tea = lc.create_tea(lc.lipidcane_sys, IncentivesTEA)
            tea.state = state
            tea.with_federal_incentives = True
            prices_by_state_with_federal[state] = lc.ethanol.price = tea.solve_price(lc.ethanol)
            prices_by_state_with_federal[state] *= 2.98668849 # USD/gal
            tea.with_federal_incentives = False
            prices_by_state_without_federal[state] = lc.ethanol.price = tea.solve_price(lc.ethanol)
            prices_by_state_without_federal[state] *= 2.98668849 # USD/gal
            

# for kind in ("with federal", "without federal"):
#     with pd.ExcelWriter(os.path.join(folder, f'Incentives {kind}.xlsx')) as writer:
#         for state in available_states:
#             tea.state = state
#             tea.with_federal_incentives = include_federal = kind == "with federal"
#             prices_by_state_with_federal[state] = lc.ethanol.price = tea.solve_price(lc.ethanol)
#             prices_by_state_with_federal[state] *= 2.98668849 # USD/gal
#             df = tea.tax_incentives.calc_all_tax_incentives(df=True, include_federal=include_federal)
#             df.to_excel(writer, sheet_name=state + " incentives")
#             df = tea.get_cashflow_table()
#             df.to_excel(writer, sheet_name=state + " cash flows")
            
            
