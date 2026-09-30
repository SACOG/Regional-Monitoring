

library(arcgis)
library(sf)


## To set up environment objects permanently, run this code in console:
# usethis::edit_r_environ()
# Then set objects as needed, save, and restart the R environment


## Function -> auth_arcgis():
# Authenticate to either ArcGIS Online (agol) or Portal (portal)
# Allows for management of feature layers hosted on AGOL or Portal

# auth_arcgis("agol"  )  # ArcGIS Online work
# auth_arcgis("portal")  # Enterprise / services.sacog.org work

auth_arcgis <- function(target = c('agol', 'portal')) {

  target <- match.arg(target)

  if (target == 'agol'){
    Sys.setenv(
      ARCGIS_HOST   = Sys.getenv('ARCGIS_HOST_AGOL'),
      ARCGIS_CLIENT = Sys.getenv('ARCGIS_CLIENT_AGOL')
    )
  }

  if (target == 'portal'){
    Sys.setenv(
      ARCGIS_HOST   = Sys.getenv('ARCGIS_HOST_PORTAL'),
      ARCGIS_CLIENT = Sys.getenv('ARCGIS_CLIENT_PORTAL')
    )
  }

}



## To update layers hosted on Portal
auth_arcgis('portal')
token <- auth_code(host = Sys.getenv("ARCGIS_HOST"))
set_arc_token(token)
message("Authenticated against: ", Sys.getenv("ARCGIS_HOST"))

fl_url <- 'https://services.sacog.org/hosting/rest/services/Hosted/Birth_Rates/FeatureServer' # Birth Rates
# fl_url <- '99689339d13e47d7b17cf39958c7d100' # Item  ID also works

fl_to_update <- arc_open(fl_url)
sdf <- fl_to_update |> get_layer(1) |> arc_select()



## To update layers hosted on AGOL
auth_arcgis('agol')
token <- auth_code(host = Sys.getenv("ARCGIS_HOST"))
set_arc_token(token)
message("Authenticated against: ", Sys.getenv("ARCGIS_HOST"))

table_url <- 'https://services6.arcgis.com/YBp5dUuxCMd8W1EI/arcgis/rest/services/Pop_2_Table/FeatureServer'
table_to_update <- arc_open(table_url)
table_to_update <- table_to_update %>% get_layer('135')
df <- arc_select(table_to_update)

