
# TODO:
# I'm not sure how to connect to Portal, only AGOL works with authentification


library(askpass)
library(arcgis)
library(readxl)
library(sf)


fl_url <- 'https://sacog.maps.arcgis.com/home/item.html?id=485906206a544d4a8960c03ee3287d6f' # Marriage Status
fl_url <- 'https://sacog.maps.arcgis.com/home/item.html?id=99689339d13e47d7b17cf39958c7d100' # Birth Rates



# host='https://portal.sacog.org/portal/home/' # Portal (i think)
host=arc_host() # AGOL


Sys.setenv('ARCGIS_USER'     = askpass("Enter your AGOL username: "))
Sys.setenv('ARCGIS_PASSWORD' = askpass("Enter your AGOL password: "))



user_authentification <- auth_user(
  username=Sys.getenv('ARCGIS_USER')
  , password=Sys.getenv('ARCGIS_PASSWORD')
  , host=host
  )
set_arc_token(user_authentification)


# I think I need to get admin priviledges from Craig to update these layers on AGOL
fl_to_update <- arc_open(fl_url)
fl_to_update %>% arc_select()




truncate_layer(fl_to_update)
add_features(fl_to_update, df_acs, chunk_size=100)


