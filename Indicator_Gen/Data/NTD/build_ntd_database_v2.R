



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
path_veh     <- file.path(path_sp, 'Vehicle Inventory' )

path_transit <- file.path('C:/Users', user, 'Sacramento Area Council of Governments/Regional Monitoring and Reporting - Documents', 'Data', 'Next Gen of Mobility Solutions', 'Transit')
path_server <- file.path('//webmapping-svr/c$/inetpub/wwwroot/monitoring/Data')


# Functions
source(file.path(path_config, 'functions.R'))




# import most recent annual data files -------------------------------------------------------------------------------------------------



# Peers mapping
file_peers <- file.path(path_config, 'peer_table.csv')
df_peers <- fread(file_peers)
colnames(df_peers) <- c('NTD ID', 'Agency', 'Acronym', 'Peer Assign')

# Population
files_pop <- file.path(path_info, list.files(path_info))
df_pop <- rbindlist(lapply(files_pop, read_pop), fill=T)

# Service and Ridership
files_service <- file.path(path_service, list.files(path_service))
df_service <- rbindlist(lapply(files_service, read_service), fill=T)

# Fare Revenues
files_fares <- file.path(path_fares, list.files(path_fares))
df_fares <- rbindlist(lapply(files_fares, read_fares), fill=T)

# Operating Expenses
files_opex <- file.path(path_opex, list.files(path_opex))
df_opex <- rbindlist(lapply(files_opex, read_opex), fill=T)

# Revenue Sources
files_rev <- file.path(path_rev, list.files(path_rev))
df_rev <- rbindlist(lapply(files_rev, read_rev), fill=T)

# Vehicle Inventories
files_veh <- file.path(path_veh, list.files(path_veh))
df_veh <- rbindlist(lapply(files_veh, read_veh), fill=T)




# YoloTD???  Hey.  What's going on here?
df_pop[`NTD ID` == 90090]



# Service and ridership table -------------------------------------------------------------------------------------------------



file_pop <- file.path(path_server, 'Pop_1 DOF Counties.xlsx')
df_dof <- read_excel(file_pop, sheet='Data') %>% setDT()
df_dof <- df_dof[, .(`Household Population` = sum(`Household Population`, na.rm=TRUE)), by = .(`Year`)]
colnames(df_dof) <- c('Year', 'Service Area Pop')


# Roll up
df_service2 <- df_peers %>%
  left_join(., df_service, by = c("NTD ID"="NTD ID"), relationship = "many-to-many") %>%
  filter(`Mode` %in% ntd_modes_map & `Time Period` == 'Annual Total') %>% 
  select(`Year`,
         `NTD ID`,
         `Agency`,
         `Acronym`,
         `Peer Assign`,
         `Mode`,
         `VOMS` = `Vehicles/Passenger Cars Operated in Maximum Service`,
          `VRM` = `Actual Vehicles/Passenger Car Revenue Miles`,
          `VRH` = `Actual Vehicle/Passenger Car Revenue Hours`,
          `UPT` = `Unlinked Passenger Trips (UPT)`) %>%
  mutate(across(c(VOMS,VRM,VRH,UPT), as.numeric)) %>%
  group_by(`Year`, `NTD ID`, `Mode`) %>%
  mutate(VOMS = sum(VOMS, na.rm=TRUE),
         VRM  = sum( VRM, na.rm=TRUE),
         VRH  = sum( VRH, na.rm=TRUE),
         UPT  = sum( UPT, na.rm=TRUE)) %>%
  distinct(Mode, .keep_all = TRUE) %>%
  setDT()


df_service3 <- merge(
  df_service2,
  df_pop,
  by=c('Year', 'NTD ID'),
  all.x=T
)

df_service3_sacog <- df_service3[`Peer Assign` == 'self']
df_service3_sacog <- df_service3_sacog[, .(
  `VOMS` = sum(`VOMS`, na.rm=TRUE),
   `VRM` = sum( `VRM`, na.rm=TRUE),
   `VRH` = sum( `VRH`, na.rm=TRUE),
   `UPT` = sum( `UPT`, na.rm=TRUE),

  `Service Area Sq Miles` = sum(`Service Area Sq Miles`, na.rm=TRUE),
  `Service Area Pop` = sum(`Service Area Pop`, na.rm=TRUE)
), by= .(`Year`, `Mode`)]

# df_service3_sacog <- df_service3_sacog[, .(
#   `VOMS` = sum(`VOMS`, na.rm=TRUE),
#   `VRM` = sum( `VRM`, na.rm=TRUE),
#   `VRH` = sum( `VRH`, na.rm=TRUE),
#   `UPT` = sum( `UPT`, na.rm=TRUE)
# ), by= .(`Year`, `Mode`)]
# df_service3_sacog <- merge(
#   df_service3_sacog,
#   df_dof,
#   by=c('Year'),
#   all.x=T
# )

df_service3_sacog[, `Region` := 'SACOG 6-County Region']


df_service3[, ':='(
  VRH_per_capita = VRH/`Service Area Pop`,
  UPT_per_capita = UPT/`Service Area Pop`
)]

df_service3_sacog[, ':='(
  VRH_per_capita = VRH/`Service Area Pop`,
  UPT_per_capita = UPT/`Service Area Pop`
)]


# Indicators

df_transit1       = df_service3      [, .(`Year`, `NTD ID`, `Agency`, `Acronym`, `Peer Assign`, `Mode`, VRH, VRH_per_capita)]
df_transit1_sacog = df_service3_sacog[, .(`Year`, `Region`, `Mode`, VRH, VRH_per_capita)]

df_transit2       = df_service3      [, .(`Year`, `NTD ID`, `Agency`, `Acronym`, `Peer Assign`, `Mode`, UPT, UPT_per_capita)]
df_transit2_sacog = df_service3_sacog[, .(`Year`, `Region`, `Mode`, UPT, UPT_per_capita)]

colnames(df_transit1) <- c('Year', 'NTD ID', 'Agency', 'Acronym', 'Peer Region', 'Transit Mode', 'VRH', 'VRH Per Capita')
colnames(df_transit2) <- c('Year', 'NTD ID', 'Agency', 'Acronym', 'Peer Region', 'Transit Mode', 'UPT', 'UPT Per Capita')

colnames(df_transit1_sacog) <- c('Year', 'Region', 'Transit Mode', 'VRH', 'VRH Per Capita')
colnames(df_transit2_sacog) <- c('Year', 'Region', 'Transit Mode', 'UPT', 'UPT Per Capita')


head(df_transit1)
tail(df_transit2)


head(df_transit1_sacog)
tail(df_transit2_sacog)




# Passenger fare table -------------------------------------------------------------------------------------------------


# Roll up
df_fares2 <- df_peers %>%
  left_join(., df_fares, by = c("NTD ID"="NTD ID"), relationship = "many-to-many") %>%
  filter(`Mode` %in% ntd_modes_map) %>%
  select(`Year`,
         `NTD ID`,
         `Agency`,
         `Acronym`,
         `Peer Assign`,
         `Mode`,
         `Fare Revenues` = `Total Fares`) %>%
  group_by(`Year`, `NTD ID`, `Mode`) %>%
  mutate(`Fare Revenues` = sum(`Fare Revenues`)) %>%
  distinct(`Mode`, .keep_all = TRUE) %>%
  setDT()


df_fares3 <- merge(
  df_fares2,
  df_pop,
  by=c('Year', 'NTD ID'),
  all.x=T
)


df_fares3[, ':='(
  `Fare Revenues Per Capita` = `Fare Revenues`/`Service Area Pop`
)]


# Indicators
df_transit4 = df_fares3[, .(
  `Year`, `NTD ID`, `Agency`, `Acronym`, `Peer Assign`, `Mode`, `Fare Revenues`, `Fare Revenues Per Capita`
)]

colnames(df_transit4) <- c('Year', 'NTD ID', 'Agency', 'Acronym', 'Peer Region', 'Transit Mode', 'Fare Revenues', 'Fare Revenues Per Capita')

head(df_transit4)






# Operating expenses table -------------------------------------------------------------------------------------------------



  
  


# Roll up
df_opex2 <- df_peers %>%
  left_join(., df_opex, by = c("NTD ID"="NTD ID"), relationship = "many-to-many") %>%
  filter(`Mode` %in% ntd_modes_map & `Operating Expense Type` != "Total") %>%
  select(`Year`,
         `NTD ID`,
         `Agency`,
         `Acronym`,
         `Peer Assign`,
         `Mode`,
         `Total Operating Expenses`) %>%
  group_by(`Year`, `NTD ID`, `Mode`) %>%
  mutate(`Total Operating Expenses` = sum(`Total Operating Expenses`)) %>%
  distinct(`Mode`, .keep_all = TRUE) %>%
  setDT()



df_opex3 <- merge(
  df_opex2,
  df_pop,
  by=c('Year', 'NTD ID'),
  all.x=T
)


df_opex3[, ':='(
  `Total Operating Expenses Per Capita` = `Total Operating Expenses`/`Service Area Pop`
)]


# Indicators
df_transit5 = df_opex3[, .(
  `Year`, `NTD ID`, `Agency`, `Acronym`, `Peer Assign`, `Mode`, `Total Operating Expenses`, `Total Operating Expenses Per Capita`
)]

colnames(df_transit5) <- c('Year', 'NTD ID', 'Agency', 'Acronym', 'Peer Region', 'Transit Mode', 'Total Operating Expenses', 'Total Operating Expenses Per Capita')


head(df_transit5)





# Revenue sources table -------------------------------------------------------------------------------------------------


# Roll up
df_rev[, `NTD ID` := as.integer(`NTD ID`)]
df_rev2 <- df_peers %>% 
  left_join(., df_rev, by = c("NTD ID"="NTD ID"), relationship = "many-to-many") %>% 
  select(`Year`,
         `NTD ID`,
         `Agency`,
         `Acronym`,
         `Peer Assign`,
         `Source` = `Funding Category`,
         `Expended On` = `Funds Expended Type`,
         `Total` = `Total`) %>% 
  group_by(`Year`, `NTD ID`, `Source`, `Expended On`) %>%
  mutate(`Total` = sum(`Total`)) %>% 
  pivot_wider(
    names_from = `Expended On`,
    values_from = `Total`
  ) %>%
  select(-`Funds Earned During Period`) %>%
  setDT()



df_rev3 <- merge(
  df_rev2,
  df_pop,
  by=c('Year', 'NTD ID'),
  all.x=T
)


df_rev3[, ':='(
  `Funds Expended on Capital Per Capita` = `Funds Expended on Capital`/`Service Area Pop`,
  `Funds Expended on Operations Per Capita` = `Funds Expended on Operations`/`Service Area Pop`
)]


# Indicators
df_transit6 = df_rev3[, .(
  `Year`, `NTD ID`, `Agency`, `Acronym`, `Peer Assign`, `Source`, `Funds Expended on Capital`, `Funds Expended on Operations`, `Funds Expended on Capital Per Capita`, `Funds Expended on Operations Per Capita`
)]


colnames(df_transit6) <- c('Year', 'NTD ID', 'Agency', 'Acronym', 'Peer Region', 'Source', 'Funds Expended on Capital', 'Funds Expended on Operations', 'Funds Expended on Capital Per Capita', 'Funds Expended on Operations Per Capita')

head(df_transit6)





# Average lifetime vehicle miles -----------------------------------------------------------------------------------------------------------






df_veh2 <- df_peers %>% 
  left_join(., df_veh, by = c("NTD ID"="NTD ID"), relationship = "many-to-many") %>%
  select(`Year`,
         `NTD ID`,
         `Agency`,
         `Acronym`,
         `Peer Assign`,
         `Vehicle Type`,
         `Total Fleet Vehicles`,
         `Average Lifetime Miles per Active Vehicles`) %>% 
  group_by(`Year`, `NTD ID`, `Agency`, `Acronym`, `Peer Assign`, `Vehicle Type`) %>% 
  summarise(
    `Weighted Average Miles` = sum(`Total Fleet Vehicles` * `Average Lifetime Miles per Active Vehicles`, na.rm = TRUE) / sum(`Total Fleet Vehicles`, na.rm = TRUE), #
    `Total Fleet Vehicles` = sum(`Total Fleet Vehicles`, na.rm = TRUE)
  ) %>%
  filter(`Vehicle Type` %in% c("Light Rail Vehicle", "Bus", "Cutaway", "Over-the-road Bus", "Double Decker Bus", "Van")) %>%
  setDT()


df_veh3 <- merge(
  df_veh2,
  df_pop,
  by=c('Year', 'NTD ID'),
  all.x=T
)


df_veh3[, ':='(
  `Weighted Average Miles Per Capita` = `Weighted Average Miles`/`Service Area Pop`,
  `Total Fleet Vehicles Per Capita` = `Total Fleet Vehicles`/`Service Area Pop`
)]


# Indicators
df_transit8 <- df_veh3[, .(
  `Year`, `NTD ID`, `Agency`, `Acronym`, `Peer Assign`, `Vehicle Type`, `Weighted Average Miles`, `Total Fleet Vehicles`, `Weighted Average Miles Per Capita`, `Total Fleet Vehicles Per Capita`
)]


colnames(df_transit8) <- c('Year', 'NTD ID', 'Agency', 'Acronym', 'Peer Region', 'Vehicle Type', 'Weighted Average Miles', 'Total Fleet Vehicles', 'Weighted Average Miles Per Capita', 'Total Fleet Vehicles Per Capita')

head(df_transit8)








# Exporting -----------------------------------------------------------------------------------------------------------------------------------


print('Service:')
head(df_transit1)
print('Ridership:')
head(df_transit2)
print('Passenger Fares:')
head(df_transit4)
print('Operating Expenses:')
head(df_transit5)
print('Revenue Sources')
head(df_transit6)
print('Vehicle Inventory')
head(df_transit8)




file_pop = file.path(path_transit, glue("Population Estimates by Transit Agency.xlsx"))
write_xlsx(list('Data' = df_pop), file_pop)
file_pop = file.path(path_server, glue("Population Estimates by Transit Agency.xlsx"))
write_xlsx(list('Data' = df_pop), file_pop)




file_transit1 = file.path(path_server, glue("Transit_1 {ntd_indicators['Transit_1']} SACOG.xlsx"))
file_transit2 = file.path(path_server, glue("Transit_2 {ntd_indicators['Transit_2']} SACOG.xlsx"))

write_xlsx(list('Data' = df_transit1_sacog), file_transit1)
write_xlsx(list('Data' = df_transit2_sacog), file_transit2)




if(export==TRUE){
  
  file_transit1 = file.path(path_server, glue("Transit_1 {ntd_indicators['Transit_1']}.xlsx"))
  file_transit2 = file.path(path_server, glue("Transit_2 {ntd_indicators['Transit_2']}.xlsx"))
  file_transit4 = file.path(path_server, glue("Transit_4 {ntd_indicators['Transit_4']}.xlsx"))
  file_transit5 = file.path(path_server, glue("Transit_5 {ntd_indicators['Transit_5']}.xlsx"))
  file_transit6 = file.path(path_server, glue("Transit_6 {ntd_indicators['Transit_6']}.xlsx"))
  file_transit8 = file.path(path_server, glue("Transit_8 {ntd_indicators['Transit_8']}.xlsx"))

  write_xlsx(list('Data' = df_transit1), file_transit1)
  write_xlsx(list('Data' = df_transit2), file_transit2)
  write_xlsx(list('Data' = df_transit4), file_transit4)
  write_xlsx(list('Data' = df_transit5), file_transit5)
  write_xlsx(list('Data' = df_transit6), file_transit6)
  write_xlsx(list('Data' = df_transit8), file_transit8)
  
  
  file_transit1 = file.path(path_transit, glue("Transit_1 {ntd_indicators['Transit_1']}.xlsx"))
  file_transit2 = file.path(path_transit, glue("Transit_2 {ntd_indicators['Transit_2']}.xlsx"))
  file_transit4 = file.path(path_transit, glue("Transit_4 {ntd_indicators['Transit_4']}.xlsx"))
  file_transit5 = file.path(path_transit, glue("Transit_5 {ntd_indicators['Transit_5']}.xlsx"))
  file_transit6 = file.path(path_transit, glue("Transit_6 {ntd_indicators['Transit_6']}.xlsx"))
  file_transit8 = file.path(path_transit, glue("Transit_8 {ntd_indicators['Transit_8']}.xlsx"))
  
  write_xlsx(list('Data' = df_transit1), file_transit1)
  write_xlsx(list('Data' = df_transit2), file_transit2)
  write_xlsx(list('Data' = df_transit4), file_transit4)
  write_xlsx(list('Data' = df_transit5), file_transit5)
  write_xlsx(list('Data' = df_transit6), file_transit6)
  write_xlsx(list('Data' = df_transit8), file_transit8)
  
}



export<-TRUE

if(export==TRUE){
  
  file_transit1 = file.path(path_server, glue("Transit_1 {ntd_indicators['Transit_1']}.xlsx"))
  file_transit2 = file.path(path_server, glue("Transit_2 {ntd_indicators['Transit_2']}.xlsx"))
  
  write_xlsx(list('Data' = df_transit1), file_transit1)
  write_xlsx(list('Data' = df_transit2), file_transit2)
  
  
  file_transit1 = file.path(path_transit, glue("Transit_1 {ntd_indicators['Transit_1']}.xlsx"))
  file_transit2 = file.path(path_transit, glue("Transit_2 {ntd_indicators['Transit_2']}.xlsx"))
  
  write_xlsx(list('Data' = df_transit1), file_transit1)
  write_xlsx(list('Data' = df_transit2), file_transit2)
  
}




