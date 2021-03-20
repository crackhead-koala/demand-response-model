from pulp import *
import pandas as pd

# Initialize the model
model = LpProblem('example_problem', LpMinimize)

# Data variables
gen_units = list(range(2))
unit_data = [{'FC': 177, 'MC': 13.5, 'P_max': 220, 'suc': 100, 'sdc': 50},
             {'FC': 137, 'MC': 17.7, 'P_max':  66, 'suc':  20, 'sdc': 10}]

hours = list(range(24))
load_hour = [166.4, 156, 150.8, 145.6, 145.6, 150.8, 166.4, 197.6, 226.2,   247, 257.4,   260,
             257.4, 260,   260, 252.2, 249.6, 249.6, 241.8, 239.2, 239.2, 241.8, 226.2, 187.2]
spin_res_req_hour = 0.1

# Define variables
state_unit_hour = LpVariable.dicts('state', [(i, t) for i in gen_units for t in hours], lowBound=0, cat='Binary')
prod_unit_hour = LpVariable.dicts('production', [(i, t) for i in gen_units for t in hours], lowBound=0)
start_cost_unit_hour = LpVariable.dicts('startup_cost', [(i, t) for i in gen_units for t in hours], lowBound=0)
shut_cost_unit_hour = LpVariable.dicts('shutdown_cost', [(i, t) for i in gen_units for t in hours], lowBound=0)
spin_res_unit_hour = LpVariable.dicts('spinning_reserve', [(i, t) for i in gen_units for t in hours], lowBound=0)

# Define objective function
model += lpSum([lpSum([unit_data[i]['FC'] * state_unit_hour[i, t] + unit_data[i]['MC'] * prod_unit_hour[i, t]
                       + 0.5 * unit_data[i]['MC'] * spin_res_unit_hour[i, t] for i in gen_units])
                for t in hours])

# Market clearing constraints
for t in hours:
    model += lpSum([prod_unit_hour[i, t] for i in gen_units]) == load_hour[t]

# Startup and shutdown cost constraints
for t in hours:
    for i in gen_units:
        if t - 1 >= 0:
            model += start_cost_unit_hour[i, t] >= unit_data[i]['suc'] * (state_unit_hour[i, t]
                                                                          - state_unit_hour[i, t - 1])
        else:
            model += start_cost_unit_hour[i, t] >= unit_data[i]['suc'] * state_unit_hour[i, t]

for t in hours:
    for i in gen_units:
        if t - 1 >= 0:
            model += shut_cost_unit_hour[i, t] >= unit_data[i]['suc'] * (state_unit_hour[i, t]
                                                                         - state_unit_hour[i, t - 1])
        else:
            model += shut_cost_unit_hour[i, t] >= unit_data[i]['sdc'] * (1 - state_unit_hour[i, t])

# Spinning reserve requirement
for t in hours:
    model += lpSum([spin_res_unit_hour[i, t] for i in gen_units]) >= spin_res_req_hour * load_hour[t]

# Maximum capacity constraints
for t in hours:
    for i in gen_units:
        model += prod_unit_hour[i, t] + spin_res_unit_hour[i, t] <= state_unit_hour[i, t] * unit_data[i]['P_max']

print(model)
model.solve()
print(LpStatus[model.status])
model_solution = {'demand': load_hour}

for i in gen_units:
    model_solution['prod_unit_{0}'.format(i)] = [prod_unit_hour[i, t].value() for t in hours]
    model_solution['state_unit_{0}'.format(i)] = [state_unit_hour[i, t].value() for t in hours]
    model_solution['spin_res_unit_{0}'.format(i)] = [spin_res_unit_hour[i, t].value() for t in hours]
    model_solution['startup_cost_unit_{0}'.format(i)] = [start_cost_unit_hour[i, t].value() for t in hours]
    model_solution['shutdown_cost_unit_{0}'.format(i)] = [shut_cost_unit_hour[i, t].value() for t in hours]

results = pd.DataFrame(model_solution)

results.to_csv('model_results.csv', encoding='utf-8')




