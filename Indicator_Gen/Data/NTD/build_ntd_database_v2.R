



rm(list = ls())
gc()
options(scipen = 999)



# Prepare workspace -------------------------------------------------------------------------------------------------


export<-FALSE


# Packages
library(data.table)
library(tidyverse)
library(readxl)
library(writexl)
library(janitor)
library(glue)


# File paths
user <- Sys.getenv("USERNAME")
path_sp <- file.path('C:/Users', user, 'Sacramento Area Council of Governments/Regional Monitoring and Reporting - Documents/Process Revamp/Task 9. Collect new data/NTD')
path_git <- file.path('C:/Users', user, 'Documents/Projects/Regional-Monitoring/Indicator_Gen/Data/NTD')
path_config <- file.path(path_git, 'config')


path_info    <- file.path(path_sp, 'AgencyInfo'        )
path_service <- file.path(path_sp, 'Service'           )
path_fares   <- file.path(path_sp, 'Fares'             )
path_opex    <- file.path(path_sp, 'Operating Expenses')
path_rev     <- file.path(path_sp, 'Revenue Sources'   )


path_server <- file.path('//webmapping-svr/c$/inetpub/wwwroot/monitoring/Data')


# Functions
source(file.path(path_config, 'functions.R'))




## 0. import most recent annual data files -------------------------------------------------------------------------------------------------



# Peers mapping
file_peers <- file.path(path_config, 'peer_table.csv')
df_peers <- fread(file_peers)

# Population data
files_pop <- file.path(path_info, list.files(path_info))
df_pop <- rbindlist(lapply(files_pop, read_pop), fill=T)
df_pop <- df_pop[!is.na(ntd_id)]

# Service data
files_service <- file.path(path_service, list.files(path_service))
df_service <- rbindlist(lapply(files_service, read_service), fill=T)

# Fare data
files_fares <- file.path(path_fares, list.files(path_fares))
df_fares <- rbindlist(lapply(files_fares, read_fares), fill=T)

# Operating Expenses data
files_opex <- file.path(path_opex, list.files(path_opex))
df_opex <- rbindlist(lapply(files_opex, read_opex), fill=T)

# Revenue Sources data
files_rev <- file.path(path_rev, list.files(path_rev))
df_rev <- rbindlist(lapply(files_rev, read_rev), fill=T)





# 1. Service and ridership table -------------------------------------------------------------------------------------------------


## Roll up
df_service[, `ntd_id` := as.integer(`ntd_id`)]
df_service2 <- df_peers %>%
  left_join(., df_service, by = c("ntdid"="ntd_id"), relationship = "many-to-many") %>%
  filter(`mode` %in% ntd_modes_map) %>%
  select(year,
         ntdid,
         agency,
         acronym,
         peer_assign,
         mode = `mode`,
         VOMS = `vehicle_passenger_cars_operated_in_maximum_service`,
         VRM = `actual_vehicle_passenger_car_revenue_miles`,
         VRH = `actual_vehicle_passenger_car_revenue_hours`,
         UPT = `unlinked_passenger_trips_upt`) %>%
  mutate(across(c(VOMS,VRM,VRH,UPT), as.numeric)) %>%
  group_by(year, ntdid, mode) %>%
  mutate(VOMS = sum(VOMS),
         VRM = sum(VRM),
         VRH = sum(VRH),
         UPT = sum(UPT)) %>%
  distinct(mode, .keep_all = TRUE) %>%
  setDT()


df_service3 <- merge(
  df_service2,
  df_pop,
  by.x=c('year', 'ntdid'),
  by.y=c('year', 'ntd_id'),
  all.x=T
)


df_service3[, ':='(
  VRH_per_capita = VRH/service_area_pop,
  UPT_per_capita = UPT/service_area_pop
)]


## Indicators

df_transit1 = df_service3[, .(
  year, ntdid, agency, acronym, peer_assign, mode, VRH, VRH_per_capita
)]

df_transit2 = df_service3[, .(
  year, ntdid, agency, acronym, peer_assign, mode, UPT, UPT_per_capita
)]

colnames(df_transit1) <- c('Year', 'NTD ID', 'Agency', 'Acronym', 'Peer Region', 'Transit Mode', 'VRH', 'VRH Per Capita')
colnames(df_transit2) <- c('Year', 'NTD ID', 'Agency', 'Acronym', 'Peer Region', 'Transit Mode', 'UPT', 'UPT Per Capita')


head(df_transit1)
head(df_transit2)






# 2. Passenger fare table -------------------------------------------------------------------------------------------------


## Roll up
df_fares[, `ntd_id` := as.integer(`ntd_id`)]
df_fares2 <- df_peers %>%
  left_join(., df_fares, by = c("ntdid"="ntd_id"), relationship = "many-to-many") %>%
  filter(`mode` %in% ntd_modes_map) %>%
  select(year,
         ntdid,
         agency,
         acronym,
         peer_assign,
         mode,
         fare_revenue = `fares`) %>%
  group_by(year, ntdid, mode) %>%
  mutate(fare_revenue = sum(fare_revenue)) %>%
  distinct(mode, .keep_all = TRUE) %>%
  setDT()


df_fares3 <- merge(
  df_fares2,
  df_pop,
  by.x=c('year', 'ntdid'),
  by.y=c('year', 'ntd_id'),
  all.x=T
)


df_fares3[, ':='(
  fare_revenue_per_capita = fare_revenue/service_area_pop
)]


## Indicators
df_transit4 = df_fares3[, .(
  year, ntdid, agency, acronym, peer_assign, mode, fare_revenue, fare_revenue_per_capita
)]

colnames(df_transit4) <- c('Year', 'NTD ID', 'Agency', 'Acronym', 'Peer Region',
                           'Transit Mode', 'Fare Revenues', 'Fare Revenues Per Capita')

head(df_transit4)




# 3. Operating expenses table -------------------------------------------------------------------------------------------------


## Roll up
df_opex[, `ntd_id` := as.integer(`ntd_id`)]
df_opex2 <- df_peers %>%
  left_join(., df_opex, by = c("ntdid"="ntd_id"), relationship = "many-to-many") %>%
  filter(`mode` %in% ntd_modes_map & `operating_expense_type` == "Total") %>%
  select(year,
         ntdid,
         agency,
         acronym,
         peer_assign,
         mode,
         opex = `total_operating_expenses`) %>%
  group_by(year, ntdid, mode) %>%
  mutate(opex = sum(opex)) %>%
  distinct(mode, .keep_all = TRUE) %>%
  setDT()



df_opex3 <- merge(
  df_opex2,
  df_pop,
  by.x=c('year', 'ntdid'),
  by.y=c('year', 'ntd_id'),
  all.x=T
)


df_opex3[, ':='(
  opex_per_capita = opex/service_area_pop
)]


## Indicators
df_transit5 = df_opex3[, .(
  year, ntdid, agency, acronym, peer_assign, mode, opex, opex_per_capita
)]

colnames(df_transit5) <- c('Year', 'NTD ID', 'Agency', 'Acronym', 'Peer Region',
                           'Transit Mode', 'Operating Expenses', 'Operating Expenses Per Capita')


head(df_transit5)





# 4. Revenue sources table -------------------------------------------------------------------------------------------------


## Roll up
df_rev[, `ntd_id` := as.integer(`ntd_id`)]
df_rev2 <- df_peers %>% 
  left_join(., df_rev, by = c("ntdid"="ntd_id"), relationship = "many-to-many") %>% 
  select(year,
         ntdid,
         agency,
         acronym,
         peer_assign,
         source = `funding_category`,
         expended_on = `funds_expended_type`,
         total = `total`) %>% 
  group_by(ntdid, source, expended_on) %>%
  mutate(total = sum(total)) %>% 
  pivot_wider(
    names_from = expended_on,
    values_from = total
  ) %>%
  select(-`Funds Earned During Period`) %>%
  rename(
    ops_revenues = `Funds Expended on Operations`,
    capital_revenues = `Funds Expended on Capital`
  ) %>%
  setDT()



df_rev3 <- merge(
  df_rev2,
  df_pop,
  by.x=c('year', 'ntdid'),
  by.y=c('year', 'ntd_id'),
  all.x=T
)


df_rev3[, ':='(
  capital_revenues_per_capita = capital_revenues/service_area_pop,
  ops_revenues_per_capita = ops_revenues/service_area_pop
)]


## Indicators
df_transit6 = df_rev3[, .(
  year, ntdid, agency, acronym, peer_assign, source, capital_revenues, ops_revenues, capital_revenues_per_capita, ops_revenues_per_capita
)]

colnames(df_transit6) <- c('Year', 'NTD ID', 'Agency', 'Acronym', 'Peer Region', 'Funding Source',
                           'Funds Expended on Capital', 'Funds Expended on Operations',
                           'Funds Expended on Capital Per Capita', 'Funds Expended on Operations Per Capita')

head(df_transit6)






# 99. Exporting -------------------------------------------------------------------------------------------------


if(export==TRUE){
  
  file_transit1 = file.path(path_server, glue("Transit_1 {ntd_indicators['Transit_1']}.xlsx"))
  file_transit2 = file.path(path_server, glue("Transit_2 {ntd_indicators['Transit_2']}.xlsx"))
  file_transit4 = file.path(path_server, glue("Transit_4 {ntd_indicators['Transit_4']}.xlsx"))
  file_transit5 = file.path(path_server, glue("Transit_5 {ntd_indicators['Transit_5']}.xlsx"))
  file_transit6 = file.path(path_server, glue("Transit_6 {ntd_indicators['Transit_6']}.xlsx"))
  
  write_xlsx(list('Data' = df_transit1), file_transit1)
  write_xlsx(list('Data' = df_transit2), file_transit2)
  write_xlsx(list('Data' = df_transit4), file_transit4)
  write_xlsx(list('Data' = df_transit5), file_transit5)
  write_xlsx(list('Data' = df_transit6), file_transit6)
  
}




