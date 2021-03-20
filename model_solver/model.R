setwd('E:/HSEshka/куркур/model_solver/')

library(dplyr)
library(ggplot2)
library(tidyr)

model_data <- read.csv('model_results.csv', encoding = 'UTF-8')
names(model_data)[1] <- 'hour'
model_data_dr <- read.csv('model_results_dr.csv', encoding = 'UTF-8')
names(model_data_dr)[1] <- 'hour'

unit_data <- data.frame(unit = c(0, 1),
                        FC = c(177 * 70, 137 * 70),
                        MC = c(13.5 * 70, 17.7 * 70),
                        suc = c(100 * 70, 20 * 70),
                        sdc = c(50 * 70, 10 * 70),
                        P_max = c(220, 66))
agg_0_data <- data.frame(offer = c(0, 1, 2),
                         q = c(20.07, 13.78, 9.72),
                         c = c(12 * 70, 14 * 70, 15 * 70),
                         IC = c(20 * 70, 23 * 70, 26 * 70),
                         LRD = c(2, 4, 8))
agg_1_data <- data.frame(offer = c(0, 1, 2),
                         q = c(21.36, 14.03, 11.28),
                         c = c(12 * 70, 14 * 70, 15 * 70),
                         IC = c(22 * 70, 25 * 70, 28 * 70),
                         LRD = c(2, 4, 8))

unit_commitment <- data.frame(hour = 0:23,
                              unit_0 = model_data$state_unit_0,
                              unit_1 = model_data$state_unit_1,
                              unit_0_dr = model_data_dr$state_unit_0,
                              unit_1_dr = model_data_dr$state_unit_1)
unit_commitment <- t(unit_commitment)

model_costs <- model_data %>%
  mutate(energy_costs = prod_unit_0 * unit_data$MC[1] + prod_unit_1 * unit_data$MC[2] +
           startup_cost_unit_0 * 70 + startup_cost_unit_1 * 70) %>%
  mutate(spin_res_costs = spin_res_unit_0 * 0.5 * unit_data$MC[1] + spin_res_unit_1 * 0.5 * unit_data$MC[2]) %>%
  mutate(system_costs = energy_costs + spin_res_costs) %>%
  select(hour, demand, system_costs, energy_costs, spin_res_costs)

model_dr_costs <- model_data_dr %>%
  mutate(energy_costs_dr = prod_unit_0 * unit_data$MC[1] + prod_unit_1 * unit_data$MC[2] +
           startup_cost_unit_0 * 70 + startup_cost_unit_1 * 70) %>%
  mutate(spin_res_costs_dr = spin_res_unit_0 * 0.5 * unit_data$MC[1] + spin_res_unit_1 * 0.5 * unit_data$MC[2]) %>%
  mutate(dr_costs = dr_cost_agg_0 * 70 + dr_cost_agg_1 * 70) %>%
  mutate(system_costs_dr = energy_costs_dr + spin_res_costs_dr + dr_costs) %>%
  mutate(system_dr = load_red_agg_0 + load_red_agg_1) %>%
  mutate(demand_dr = demand - system_dr) %>%
  select(hour, demand, demand_dr, system_dr, system_costs_dr, energy_costs_dr, spin_res_costs_dr, dr_costs)

cost_structure <- model_costs %>%
  summarize(energy_costs = sum(energy_costs), spin_res_costs = sum(spin_res_costs),
            total_costs = sum(system_costs))

cost_structure_dr <- model_dr_costs %>%
  summarize(energy_costs_dr = sum(energy_costs_dr), spin_res_costs_dr = sum(spin_res_costs_dr),
            dr_costs = sum(dr_costs), total_costs_dr = sum(system_costs_dr))

model_results <- cbind(model_dr_costs, model_costs$system_costs)
names(model_results)[9] <- 'system_costs'

model_results <- model_results %>%
  mutate(costs_rel_change = 100 * (system_costs - system_costs_dr) / system_costs) %>%
  mutate(load_rel_change = 100 * (demand - demand_dr) / demand)

model_results_long <- gather(model_results, key = 'case', value = 'load', demand, demand_dr)
model_results_long_costs <- gather(model_results, key = 'case', value = 'costs',
                                   system_costs, system_costs_dr)

ggplot(model_results_long_costs, aes(x = hour, y = costs, fill = case)) +
  geom_col(position = 'dodge') +
  scale_x_continuous(breaks = seq(0, 23, by = 2)) +
  xlab('Hour (h)') +
  ylab('Total System Costs (rub)') +
  scale_fill_discrete(name = '', labels = c('Case 1 (no DR)', 'Case 2 (DR)')) +
  theme_test()

ggplot(model_results_long_costs, aes(x = hour, y = costs, color = case)) +
  geom_line() +
  geom_point() +
  scale_x_continuous(breaks = seq(0, 23, by = 2)) +
  scale_y_continuous(breaks = seq(100000, 300000, by = 50000), limits = c(100000, 300000)) +
  xlab('Hour (h)') +
  ylab('Total System Costs (rub)') +
  scale_fill_discrete(name = '', labels = c('Case 1 (no DR)', 'Case 2 (DR)')) +
  theme_test()

ggplot(model_results, aes(x = hour, y = costs_rel_change)) +
  geom_col() +
  scale_x_continuous(breaks = seq(0, 23, by = 2)) +
  xlab('Hour (h)') +
  ylab('Total System Costs Relative Change (%)') +
  theme_test()

ggplot(model_results_long, aes(x = hour, y = load, fill = case)) +
  geom_col(position = 'dodge') +
  scale_x_continuous(breaks = seq(0, 23, by = 2)) +
  scale_y_continuous(breaks = seq(0, 280, by = 60)) +
  xlab('Hour (h)') +
  ylab('Total System Load (MW)') +
  scale_fill_discrete(name = '', labels = c('Case 1 (no DR)', 'Case 2 (DR)')) +
  theme_test()

ggplot(model_results, aes(x = hour, y = load_rel_change)) +
  geom_col() +
  scale_x_continuous(breaks = seq(0, 23, by = 2)) +
  xlab('Hour (h)') +
  ylab('Total System Load Relative Change (%)') +
  theme_test()

ggplot(model_results, aes(x = hour, y = system_dr)) +
  geom_col() +
  scale_x_continuous(breaks = seq(0, 23, by = 2)) +
  xlab('Hour (h)') +
  ylab('Load Reduction (MW)') +
  theme_test()

sum(model_results$load_rel_change) / 10
sum(model_results$costs_rel_change) / sum(!(model_results$costs_rel_change == 0))


