


# User defined objects/functions for NTD processing

ntd_modes_map <- c(
  light_rail = "LR",
  urban_bus = "MB",
  commuter_bus = "CB",
  demand_response = "DR"
)


ntd_indicators <- c(
  Transit_1 = 'Service Hours',
  Transit_2 = 'Ridership',
  Transit_4 = 'Fares',
  Transit_5 = 'Operating Expenses',
  Transit_6 = 'Revenue Sources',
  Transit_8 = 'Vehicle Inventories'
)


apply_ntdid_cw <- function(year_file, df){
  
  if(year_file <= 2013){
    file_cw <- file.path(path_info, '2014 Agency Information.xlsx')
    df_ntd_cw <- read_excel(file_cw) %>% select(`5 digit NTDID`, `4 digit NTDID`) %>% unique() %>% setDT()
    df_ntd_cw[, `:=`(`5 digit NTDID` = as.integer(`5 digit NTDID`), `4 digit NTDID` = as.integer(`4 digit NTDID`))]
    df[, `NTD ID` := as.integer(`NTD ID`)]
    df <- merge(df, df_ntd_cw, by.x='NTD ID', by.y='4 digit NTDID', all.x=TRUE)
    df[, `NTD ID` := `5 digit NTDID`]
    df$`5 digit NTDID` <- NULL
  }
  return(df)
}





read_pop <- function(file){
  
  file_cols <- file.path(path_config, 'cols.xlsx')
  year_file <- as.integer(gsub(" Agency Information.xlsx", "", basename(file)))
  cols_year <- c(as.character(year_file))
  
  df_cols <- read_excel(file_cols, sheet='AgencyInfo') %>% setDT()
  cols_final <- c(df_cols[['2024']])
  cols_year <- c(df_cols[[cols_year]])
  
  df <- read_excel(file)
  df <- df[cols_year]
  colnames(df) <- cols_final
  df <- df %>% 
    select(`NTD ID`,
           `Service Area Sq Miles`,
           `Service Area Pop`)
  df <- df %>% mutate(Year = as.integer(gsub(" Agency Information.xlsx", "", basename(file))),
                      `NTD ID` = as.integer(`NTD ID`))
  
  setDT(df)
  df <- apply_ntdid_cw(year_file, df)
  
  df <- df[!is.na(`NTD ID`)]
  
  return(df)
  
}




read_service <- function(file){
  
  file_cols <- file.path(path_config, 'cols.xlsx')
  year_file <- as.integer(gsub(" Service.xlsx", "", basename(file)))
  year_cols <- c(as.character(year_file))

  df_cols <- read_excel(file_cols, sheet='Service') %>% setDT()
  cols_final <- c(df_cols[['2024']])
  cols_year <- c(df_cols[[`year_cols`]])
  cols_year <- Filter(Negate(is.na), cols_year)

  df <- read_excel(file)
  if(year_file <= 2011){
    if(year_file <= 2011 & year_file >= 2008){
      df <- df %>% mutate(
        `Vehicle_Or_Train_Rev_Miles` = case_when(Mode_Cd == 'LR' ~     `Passenger_Car_Rev_Miles`, Mode_Cd != 'LR' ~ `Vehicle_Or_Train_Rev_Miles`),
        `Vehicle_Or_Train_Rev_Hours` = case_when(Mode_Cd == 'LR' ~ `Passenger_Car_Revenue_Hours`, Mode_Cd != 'LR' ~ `Vehicle_Or_Train_Rev_Hours`)
      )
    }
    if(year_file <= 2007 & year_file >= 2003){
      df <- df %>% mutate(
        `vehicle_Or_Train_Rev_Miles` = case_when(Mode_Cd == 'LR' ~     `passenger_Car_Rev_Miles`, Mode_Cd != 'LR' ~ `vehicle_Or_Train_Rev_Miles`),
        `Vehicle_Or_Train_Rev_Hours` = case_when(Mode_Cd == 'LR' ~ `Passenger_Car_Revenue_Hours`, Mode_Cd != 'LR' ~ `Vehicle_Or_Train_Rev_Hours`)
      )
    }
    if(year_file == 2002){
      df <- df %>% mutate(
        `VEH_REV_MILES_NUM` = case_when(MODE_CD == 'LR' ~ `PASS_CAR_REV_MILES_NUM`, MODE_CD != 'LR' ~ `VEH_REV_MILES_NUM`),
        `VEH_REV_HOURS_NUM` = case_when(MODE_CD == 'LR' ~   `PASS_CAR_REV_HRS_NUM`, MODE_CD != 'LR' ~ `VEH_REV_HOURS_NUM`)
      )
    }
  }
  
  df <- df[cols_year]
  colnames(df) <- cols_final
  setDT(df)
  df <- apply_ntdid_cw(year_file, df)
  
  # df = df[`Vehicles/Passenger Cars Operated in Maximum Service`!='-']
  df[, Year := year_file]
  df[, ':='(
    `NTD ID` = as.integer(`NTD ID`)
       , `Vehicles/Passenger Cars Operated in Maximum Service` = as.numeric(`Vehicles/Passenger Cars Operated in Maximum Service`)
       , `Actual Vehicles/Passenger Car Revenue Miles`  = as.numeric(`Actual Vehicles/Passenger Car Revenue Miles`)
       , `Actual Vehicle/Passenger Car Revenue Hours`  = as.numeric(`Actual Vehicle/Passenger Car Revenue Hours`)
       , `Unlinked Passenger Trips (UPT)`  = as.numeric(`Unlinked Passenger Trips (UPT)`)
    )
  ] 
  
  
  return(df)
}





read_fares <- function(file){
  
  
  file_cols <- file.path(path_config, 'cols.xlsx')
  year_file <- as.integer(gsub(" Fare Revenues.xlsx", "", basename(file)))
  cols_year <- c(as.character(year_file))
  
  df_cols <- read_excel(file_cols, sheet='Fares') %>% setDT()
  cols_final <- c(df_cols[['2024']])
  cols_year <- c(df_cols[[cols_year]])
  
  df <- read_excel(file)
  df <- df[cols_year]
  colnames(df) <- cols_final
  setDT(df)
  df <- apply_ntdid_cw(year_file, df)
  
  df <- df %>% mutate(Year = year_file)
  df[, `NTD ID` := as.integer(`NTD ID`)]
  df[, `Total Fares` := as.integer(`Total Fares`)]
  
  
  return(df)
  
}






read_opex <- function(file){
  
  file_cols <- file.path(path_config, 'cols.xlsx')
  year_file <- as.integer(gsub(" Operating Expenses.xlsx", "", basename(file)))
  year_col <- c(as.character(year_file))
  
  df_cols <- read_excel(file_cols, sheet='Operating Expenses') %>% setDT()
  cols_2024 <- c(df_cols[['2024']])
  cols_2024 <- Filter(Negate(is.na), cols_2024)

  cols_year <- c(df_cols[[`year_col`]])
  cols_year <- Filter(Negate(is.na), cols_year)
  
  expenses_to_remove <- c('Total Operating Expenses', 'Total Operating Expenses (No Funds Reported Separately)', 'Total Modal Expenses', 'Total_Modal_Expenses')
  cols_year <- cols_year[!cols_year %in% expenses_to_remove]
  cols_expenses <- cols_year[!cols_year %in% cols_year[1:3]]
  
  df <- read_excel(file)
  df <- df[cols_year]
  setDT(df)
  df[, (cols_expenses) := lapply(.SD, as.numeric), .SDcols = cols_expenses]
  df <- df[, .(total_expenses = rowSums(.SD, na.rm=TRUE)), by=eval(cols_year[1:3])]
  colnames(df) <- c('NTD ID', 'Mode', 'Operating Expense Type', 'Total Operating Expenses')
  df <- apply_ntdid_cw(year_file, df)
  
  df <- df %>% mutate(Year = year_file)
  df[, `NTD ID` := as.integer(`NTD ID`)]
  df[, `Total Operating Expenses` := as.integer(`Total Operating Expenses`)]
  
  return(df)
}




read_rev <- function(file){
  
  
  file_cols <- file.path(path_config, 'cols.xlsx')
  year_file <- as.integer(gsub(" Revenue Sources.xlsx", "", basename(file)))
  cols_year <- c(as.character(year_file))
  
  df_cols <- read_excel(file_cols, sheet='Revenue Sources') %>% setDT()
  cols_final <- c(df_cols[['2024']])
  cols_year <- c(df_cols[[cols_year]])
  
  df <- read_excel(file)
  df <- df[cols_year]
  colnames(df) <- cols_final
  setDT(df)
  df <- apply_ntdid_cw(year_file, df)
  
  df <- df %>% mutate(Year = year_file)
  df[, `NTD ID` := as.integer(`NTD ID`)]
  df[, `Total` := as.integer(`Total`)]
  
  return(df)
}





read_veh <- function(file){
  
  
  file_cols <- file.path(path_config, 'cols.xlsx')
  year_file <- as.integer(gsub(" Revenue Vehicle Inventory.xlsx", "", basename(file)))
  cols_year <- c(as.character(year_file))

  df_cols <- read_excel(file_cols, sheet='Vehicle Inventory') %>% setDT()
  cols_final <- c(df_cols[['2024']])
  cols_year <- c(df_cols[[cols_year]])
  
  df <- read_excel(file)
  df <- df[cols_year]
  colnames(df) <- cols_final
  setDT(df)
  df <- apply_ntdid_cw(year_file, df)
  
  df <- df %>% mutate(Year = year_file)
  df[, `NTD ID` := as.integer(`NTD ID`)]
  df[, ':='(
    `Total Fleet Vehicles` = as.numeric(`Total Fleet Vehicles`),
    `Average Lifetime Miles per Active Vehicles` = as.numeric(`Average Lifetime Miles per Active Vehicles`)
  )]
  
  # "Buses", "Vans", "Light rail vehicles (Streetcars)", "Trolleybuses", "Double decked buses", "Taxicab van"?
  df[`Vehicle Type` ==                            'Buses', `Vehicle Type` :=                'Bus']
  df[`Vehicle Type` ==                             'Vans', `Vehicle Type` :=                'Van']
  df[`Vehicle Type` == 'Light rail vehicles (Streetcars)', `Vehicle Type` := 'Light Rail Vehicle']
  df[`Vehicle Type` ==              'Double decked buses', `Vehicle Type` :=  'Double Decker Bus']
  
  return(df)
  
}







# Code Graveyard ----------------------------------------------------------------------------------------------------------------------------------------------------------

# # User defined objects/functions for NTD processing
# 
# ntd_modes_map <- c(
#   light_rail = "LR",
#   urban_bus = "MB",
#   commuter_bus = "CB",
#   demand_response = "DR"
# )
# 
# 
# ntd_indicators <- c(
#   Transit_1 = 'Service Hours',
#   Transit_2 = 'Ridership',
#   Transit_4 = 'Fares',
#   Transit_5 = 'Operating Expenses',
#   Transit_6 = 'Revenue Sources'
# )
# 
# 
# 
# 
# 
# read_pop <- function(file){
#   
#   df <- read_excel(file)
#   df <- clean_names(df)
#   col_names <- colnames(df)
#   col_names <- gsub('x5_digit_ntd_id', 'ntd_id', col_names)
#   col_names <- gsub('x5_digit_ntdid' , 'ntd_id', col_names)
#   col_names <- gsub('service_area_sq_miles', 'service_area_sq_mi', col_names)
#   colnames(df) <- col_names
#   df <- df %>%
#     select(`ntd_id`,
#            `service_area_sq_mi`,
#            `service_area_pop`)
#   df <- df %>% mutate(year = as.integer(gsub(" Agency Information.xlsx", "", basename(file))),
#                       ntd_id = as.integer(ntd_id))
#   setDT(df)
#   df <- df[!is.na(ntd_id)]
#   
#   
#   return(df)
# }
# 
# 
# 
# read_service <- function(file){
#   
#   df <- read_excel(file)
#   df <- clean_names(df)
#   col_names <- colnames(df)
#   col_names <- gsub('x5_digit_ntd_id', 'ntd_id', col_names)
#   col_names <- gsub('x5_digit_ntdid' , 'ntd_id', col_names)
#   col_names <- gsub('vehicles', 'vehicle', col_names)
#   col_names <- gsub('_car_deadhead_', '_deadhead_', col_names)
#   colnames(df) <- col_names
#   df <- df %>% filter(`time_period` == "Annual Total")
#   df <- df %>% mutate(year = as.integer(gsub(" Service.xlsx", "", basename(file))))
#   setDT(df)
#   
#   return(df)
# }
# 
# 
# 
# # read_fares <- function(file){
# #   
# #   df <- read_excel(file)
# #   df <- clean_names(df)
# #   col_names <- colnames(df)
# #   col_names <- gsub('total_fares', 'fares', col_names)
# #   colnames(df) <- col_names
# #   df <- df %>% mutate(year = as.integer(gsub(" Fare Revenues.xlsx", "", basename(file))))
# #   setDT(df)
# #   
# #   return(df)
# # }
# 
# 
# 
# read_fares <- function(file, file_cols){
#   
#   
#   file_cols <- file.path(path_config, 'cols.xlsx')
#   year_file <- as.integer(gsub(" Fare Revenues.xlsx", "", basename(file)))
#   cols_year <- c(as.character(year_file))
#   
#   df_cols <- read_excel(file_cols, sheet='Fares') %>% setDT()
#   cols_final <- c(df_cols[['2024']])
#   cols_year <- c(df_cols[[cols_year]])
#   
#   
#   df <- read_excel(file, col_types="text")
#   df <- df[cols_year]
#   colnames(df) <- cols_final
#   df <- df %>% mutate(year = year_file)
#   setDT(df)
#   df[, `NTD ID` := str_pad(`NTD ID`, width = 5, pad = "0", side = "left")]
#   
#   
#   return(df)
# }
# 
# 
# 
# 
# 
# 
# read_opex <- function(file){
#   
#   df <- read_excel(file)
#   df <- clean_names(df)
#   df <- df %>% mutate(year = as.integer(gsub(" Operating Expenses.xlsx", "", basename(file))))
#   setDT(df)
#   
#   return(df)
# }
# 
# 
# 
# 
# read_rev <- function(file){
#   
#   df <- read_excel(file)
#   df <- clean_names(df)
#   col_names <- colnames(df)
#   col_names <- gsub('total_of_fares', 'total', col_names)
#   colnames(df) <- col_names
#   df <- df %>% mutate(year = as.integer(gsub(" Revenue Sources.xlsx", "", basename(file))))
#   setDT(df)
#   
#   return(df)
# }










