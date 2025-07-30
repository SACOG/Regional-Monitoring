


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
  Transit_6 = 'Revenue Sources'
)


read_pop <- function(file){
  
  df <- read_excel(file)
  df <- clean_names(df)
  col_names <- colnames(df)
  col_names <- gsub('x5_digit_ntd_id', 'ntd_id', col_names)
  col_names <- gsub('x5_digit_ntdid' , 'ntd_id', col_names)
  col_names <- gsub('service_area_sq_miles', 'service_area_sq_mi', col_names)
  colnames(df) <- col_names
  df <- df %>%
    select(`ntd_id`,
           `service_area_sq_mi`,
           `service_area_pop`)
  df <- df %>% mutate(year = as.integer(gsub(" Agency Information.xlsx", "", basename(file))),
                      ntd_id = as.integer(ntd_id))
  setDT(df)
  
  return(df)
}



read_service <- function(file){
  
  df <- read_excel(file)
  df <- clean_names(df)
  col_names <- colnames(df)
  col_names <- gsub('x5_digit_ntd_id', 'ntd_id', col_names)
  col_names <- gsub('x5_digit_ntdid' , 'ntd_id', col_names)
  col_names <- gsub('vehicles', 'vehicle', col_names)
  col_names <- gsub('_car_deadhead_', '_deadhead_', col_names)
  colnames(df) <- col_names
  df <- df %>% filter(`time_period` == "Annual Total")
  df <- df %>% mutate(year = as.integer(gsub(" Service.xlsx", "", basename(file))))
  setDT(df)
  
  return(df)
}



read_fares <- function(file){
  
  df <- read_excel(file)
  df <- clean_names(df)
  col_names <- colnames(df)
  col_names <- gsub('total_fares', 'fares', col_names)
  colnames(df) <- col_names
  df <- df %>% mutate(year = as.integer(gsub(" Fare Revenues.xlsx", "", basename(file))))
  setDT(df)
  
  return(df)
}



read_opex <- function(file){
  
  df <- read_excel(file)
  df <- clean_names(df)
  df <- df %>% mutate(year = as.integer(gsub(" Operating Expenses.xlsx", "", basename(file))))
  setDT(df)
  
  return(df)
}




read_rev <- function(file){
  
  df <- read_excel(file)
  df <- clean_names(df)
  col_names <- colnames(df)
  col_names <- gsub('total_of_fares', 'total', col_names)
  colnames(df) <- col_names
  df <- df %>% mutate(year = as.integer(gsub(" Revenue Sources.xlsx", "", basename(file))))
  setDT(df)
  
  return(df)
}

