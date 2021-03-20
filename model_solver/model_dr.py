from pulp import *
import pandas as pd

# Initialize the model
model_dr = LpProblem('example_problem', LpMinimize)

# Data variables
gen_units = list(range(2))
unit_data = [{'FC': 177, 'MC': 13.5, 'P_max': 220, 'suc': 100, 'sdc': 50},
             {'FC': 137, 'MC': 17.7, 'P_max':  66, 'suc':  20, 'sdc': 10}]

hours = list(range(24))
load_hour = [166.4, 156, 150.8, 145.6, 145.6, 150.8, 166.4, 197.6, 226.2,   247, 257.4,   260,
             257.4, 260,   260, 252.2, 249.6, 249.6, 241.8, 239.2, 239.2, 241.8, 226.2, 187.2]
spin_res_req_hour = 0.1

aggs = list(range(2))
offers = list(range(3))
agg_data = [[{'q': 20.07, 'c': 12, 'IC': 20, 'LRD': 2, 'MN': 1},
             {'q': 13.78, 'c': 14, 'IC': 23, 'LRD': 4, 'MN': 1},
             {'q':  9.72, 'c': 15, 'IC': 26, 'LRD': 8, 'MN': 1}],
            [{'q': 21.36, 'c': 12, 'IC': 22, 'LRD': 2, 'MN': 1},
             {'q': 14.03, 'c': 14, 'IC': 25, 'LRD': 4, 'MN': 1},
             {'q': 11.28, 'c': 15, 'IC': 28, 'LRD': 8, 'MN': 1}]]

# Define variables
state_unit_hour = LpVariable.dicts('state', [(i, t) for i in gen_units for t in hours], lowBound=0, cat='Binary')
prod_unit_hour = LpVariable.dicts('production', [(i, t) for i in gen_units for t in hours], lowBound=0)
start_cost_unit_hour = LpVariable.dicts('startup_cost', [(i, t) for i in gen_units for t in hours], lowBound=0)
shut_cost_unit_hour = LpVariable.dicts('shutdown_cost', [(i, t) for i in gen_units for t in hours], lowBound=0)
spin_res_unit_hour = LpVariable.dicts('spinning_reserve', [(i, t) for i in gen_units for t in hours], lowBound=0)

dr_cost_agg_hour = LpVariable.dicts('dr_cost', [(d, t) for d in aggs for t in hours], lowBound=0)
load_red_agg_hour = LpVariable.dicts('load_red', [(d, t) for d in aggs for t in hours], lowBound=0)
dr_init_cost_off_agg_hour = LpVariable.dicts('dr_init_cost', [(k, d, t) for k in offers for d in aggs for t in hours],
                                             lowBound=0)
u_off_agg_hour = LpVariable.dicts('u', [(k, d, t) for k in offers for d in aggs for t in hours], lowBound=0,
                                  cat='Binary')
y_off_agg_hour = LpVariable.dicts('y', [(k, d, t) for k in offers for d in aggs for t in hours], lowBound=0,
                                  cat='Binary')
z_off_agg_hour = LpVariable.dicts('z', [(k, d, t) for k in offers for d in aggs for t in hours], lowBound=0,
                                  cat='Binary')

# Define objective function
model_dr += lpSum([lpSum([unit_data[i]['FC'] * state_unit_hour[i, t] + unit_data[i]['MC'] * prod_unit_hour[i, t]
                          + 0.5 * unit_data[i]['MC'] * spin_res_unit_hour[i, t] for i in gen_units])
                   + lpSum([dr_cost_agg_hour[d, t] for d in aggs])
                   for t in hours])

# Market clearing constraints
for t in hours:
    model_dr += lpSum([prod_unit_hour[i, t] for i in gen_units]) == \
                load_hour[t] - lpSum([load_red_agg_hour[d, t] for d in aggs])

# Startup and shutdown cost constraints
for t in hours:
    for i in gen_units:
        if t - 1 >= 0:
            model_dr += start_cost_unit_hour[i, t] >= unit_data[i]['suc'] * (state_unit_hour[i, t]
                                                                             - state_unit_hour[i, t - 1])
        else:
            model_dr += start_cost_unit_hour[i, t] >= unit_data[i]['suc'] * state_unit_hour[i, t]

for t in hours:
    for i in gen_units:
        if t - 1 >= 0:
            model_dr += shut_cost_unit_hour[i, t] >= unit_data[i]['suc'] * (state_unit_hour[i, t]
                                                                            - state_unit_hour[i, t - 1])
        else:
            model_dr += shut_cost_unit_hour[i, t] >= unit_data[i]['sdc'] * (1 - state_unit_hour[i, t])

# Spinning reserve requirement
for t in hours:
    model_dr += lpSum([spin_res_unit_hour[i, t] for i in gen_units]) >= spin_res_req_hour * load_hour[t]

# Maximum capacity constraints
for t in hours:
    for i in gen_units:
        model_dr += prod_unit_hour[i, t] + spin_res_unit_hour[i, t] <= state_unit_hour[i, t] * unit_data[i]['P_max']

# DR constraints
for t in hours:
    for d in aggs:
        model_dr += dr_cost_agg_hour[d, t] == lpSum([dr_init_cost_off_agg_hour[k, d, t] + agg_data[d][k]['c'] *
                                                     agg_data[d][k]['q'] * u_off_agg_hour[k, d, t] for k in offers])

for t in hours:
    for d in aggs:
        model_dr += load_red_agg_hour[d, t] == lpSum([agg_data[d][k]['q'] * u_off_agg_hour[k, d, t] for k in offers])

for t in hours:
    for d in aggs:
        for k in offers:
            if t - 1 >= 0:
                model_dr += y_off_agg_hour[k, d, t] - z_off_agg_hour[k, d, t] == u_off_agg_hour[k, d, t] \
                            - u_off_agg_hour[k, d, t - 1]
            else:
                model_dr += y_off_agg_hour[k, d, t] - z_off_agg_hour[k, d, t] == u_off_agg_hour[k, d, t]

for t in hours:
    for d in aggs:
        for k in offers:
            model_dr += y_off_agg_hour[k, d, t] + z_off_agg_hour[k, d, t] <= 1

for t in hours:
    for d in aggs:
        for k in offers:
            model_dr += dr_init_cost_off_agg_hour[k, d, t] >= agg_data[d][k]['IC'] * y_off_agg_hour[k, d, t]

# DR duration lower limit
for t in hours:
    for d in aggs:
        for k in offers:
            if t + agg_data[d][k]['LRD'] < 24:
                model_dr += lpSum([u_off_agg_hour[k, d, t_] for t_ in range(t, t + agg_data[d][k]['LRD'])]) >= \
                            agg_data[d][k]['LRD'] * y_off_agg_hour[k, d, t]
            else:
                model_dr += lpSum([u_off_agg_hour[k, d, t_] for t_ in range(t, 24)]) >= \
                            (24 - t) * y_off_agg_hour[k, d, t]

# DR duration upper limit
for t in hours:
    for d in aggs:
        for k in offers:
            if t + agg_data[d][k]['LRD'] < 24:
                model_dr += lpSum([z_off_agg_hour[k, d, t_] for t_ in range(t, t + agg_data[d][k]['LRD'] + 1)]) >= \
                            y_off_agg_hour[k, d, t]
            else:
                model_dr += lpSum([z_off_agg_hour[k, d, t_] for t_ in range(t, 24)]) >= y_off_agg_hour[k, d, t]

# Restriction on the number of daily DR
for d in aggs:
    for k in offers:
        model_dr += lpSum([y_off_agg_hour[k, d, t] for t in hours]) <= agg_data[d][k]['MN']

# Print the model
print(model_dr)

# Solve the model, print status (Optimal/Infeasible)
model_dr.solve()
print(LpStatus[model_dr.status])

# Get values for variables as a data frame
model_solution = {'demand': load_hour}

for i in gen_units:
    model_solution['prod_unit_{0}'.format(i)] = [prod_unit_hour[i, t].value() for t in hours]
    model_solution['state_unit_{0}'.format(i)] = [state_unit_hour[i, t].value() for t in hours]
    model_solution['spin_res_unit_{0}'.format(i)] = [spin_res_unit_hour[i, t].value() for t in hours]
    model_solution['startup_cost_unit_{0}'.format(i)] = [start_cost_unit_hour[i, t].value() for t in hours]
    model_solution['shutdown_cost_unit_{0}'.format(i)] = [shut_cost_unit_hour[i, t].value() for t in hours]

for d in aggs:
    model_solution['load_red_agg_{0}'.format(d)] = [load_red_agg_hour[d, t].value() for t in hours]
    model_solution['dr_cost_agg_{0}'.format(d)] = [dr_cost_agg_hour[d, t].value() for t in hours]

    for k in offers:
        model_solution['dr_init_cost_agg_{0}_off_{1}'.format(d, k)] = [dr_init_cost_off_agg_hour[k, d, t].value()
                                                                       for t in hours]
        model_solution['u_agg_{0}_off_{1}'.format(d, k)] = [u_off_agg_hour[k, d, t].value() for t in hours]
        model_solution['y_agg_{0}_off_{1}'.format(d, k)] = [y_off_agg_hour[k, d, t].value() for t in hours]
        model_solution['z_agg_{0}_off_{1}'.format(d, k)] = [z_off_agg_hour[k, d, t].value() for t in hours]

results = pd.DataFrame(model_solution)
results.to_csv('model_results_dr.csv', encoding='utf-8')




