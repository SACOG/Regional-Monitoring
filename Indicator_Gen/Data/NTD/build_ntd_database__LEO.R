library(tidyverse)
library(here)

# 0. import most recent annual data files

service_data <- readxl::read_excel(path = here("raw_data", "2023 Service.xlsx")) %>% 
  filter(`Time Period` == "Annual Total")

fare_data <- readxl::read_excel(path = here("raw_data", "2023 Fare Revenues.xlsx"))

opex_data <- readxl::read_excel(path = here("raw_data", "2023 Operating Expenses.xlsx"))

revenue_data <- readxl::read_excel(path = here("raw_data", "2023 Revenue Sources.xlsx"))

pop_data <- readxl::read_excel(path = here("raw_data", "2023 Agency Information.xlsx")) %>% 
  mutate(`NTD ID` = as.numeric(`NTD ID`))

vehinventory_data <- readxl::read_excel(path = here("raw_data", "2023 Revenue Vehicle Inventory.xlsx"))

# 1. Service and ridership table

service_upt_peers <- peer_table %>% 
  left_join(., service_data, by = c("ntdid"="NTD ID"), relationship = "many-to-many") %>% 
  filter(`Mode` %in% ntd_modes_map) %>% 
  select(ntdid,
         agency,
         acronym,
         peer_assign,
         mode = `Mode`,
         VOMS = `Vehicles/Passenger Cars Operated in Maximum Service`,
         VRM = `Actual Vehicles/Passenger Car Revenue Miles`,
         VRH = `Actual Vehicle/Passenger Car Revenue Hours`,
         UPT = `Unlinked Passenger Trips (UPT)`) %>% 
  mutate(across(c(VOMS,VRM,VRH,UPT), as.numeric)) %>% 
  group_by(ntdid, mode) %>%
  mutate(VOMS = sum(VOMS),
         VRM = sum(VRM),
         VRH = sum(VRH),
         UPT = sum(UPT)) %>% 
  distinct(mode, .keep_all = TRUE)

write_csv(service_upt_peers, here("tables", "service_upt_peers.csv"))

# 2. Passenger fare table
fares_peers <- peer_table %>% 
  left_join(., fare_data, by = c("ntdid"="NTD ID"), relationship = "many-to-many") %>% 
  filter(`Mode` %in% ntd_modes_map) %>% 
  select(ntdid,
         agency,
         acronym,
         peer_assign,
         mode = `Mode`,
         fare_revenue = `Total Fares`) %>% 
  group_by(ntdid, mode) %>%
  mutate(fare_revenue = sum(fare_revenue)) %>% 
  distinct(mode, .keep_all = TRUE)

write_csv(fares_peers, here("tables", "fares_peers.csv"))

# 3. Operating expenses table
opex_peers <- peer_table %>% 
  left_join(., opex_data, by = c("ntdid"="NTD ID"), relationship = "many-to-many") %>% 
  filter(`Mode` %in% ntd_modes_map & `Operating Expense Type` == "Total") %>% 
  select(ntdid,
         agency,
         acronym,
         peer_assign,
         mode = `Mode`,
         opex = `Total Operating Expenses`) %>% 
  group_by(ntdid, mode) %>%
  mutate(opex = sum(opex)) %>% 
  distinct(mode, .keep_all = TRUE)

write_csv(opex_peers, here("tables", "opex_peers.csv"))

# 4. Revenue sources table
revenues_peers <- peer_table %>% 
  left_join(., revenue_data, by = c("ntdid"="NTD ID"), relationship = "many-to-many") %>% 
  select(ntdid,
         agency,
         acronym,
         peer_assign,
         source = `Funding Category`,
         expended_on = `Funds Expended Type`,
         total = `Total`) %>% 
  group_by(ntdid, source, expended_on) %>%
  mutate(total = sum(total)) %>% 
  pivot_wider(
    names_from = expended_on,
    values_from = total
  ) %>% 
  select(-`Funds Earned During Period`, -`NA`) %>%
  rename(
    ops_revenues = `Funds Expended on Operations`,
    capital_revenues = `Funds Expended on Capital`
  )

# 5. Service area population table
population_peers <- peer_table %>% 
  left_join(., pop_data, by = c("ntdid"="NTD ID")) %>% 
  select(ntdid,
         agency,
         acronym,
         peer_assign,
         sq_mi = `Service Area Sq Miles`,
         population = `Service Area Pop`)

# 6. Average lifetime vehicle miles
vehinventory_peers <- peer_table %>% 
  left_join(., vehinventory_data, by = c("ntdid"="NTD ID"), relationship = "many-to-many") %>%
  select(ntdid,
         agency,
         acronym,
         peer_assign,
         total_fleet = `Total Fleet Vehicles`,
         type = `Vehicle Type`,
         lifetime_miles = `Average Lifetime Miles per Active Vehicles`) %>% 
  group_by(ntdid, type) %>% 
  summarise(
    weighted_avg_miles = sum(total_fleet * lifetime_miles, na.rm = TRUE) / sum(total_fleet, na.rm = TRUE),
    total_vehicles = sum(total_fleet, na.rm = TRUE)
  ) %>%
  filter(type %in% c("Light Rail Vehicle", "Bus","Cutaway", "Over-the-road Bus", "Double Decker Bus", "Van"))