

ACS_year <- 2024
path_server <- '//webmapping-svr/c$/inetpub/wwwroot/monitoring/Data'


library(arcgis)
library(sf)
library(readxl)


auth_arcgis <- function(target = c('agol', 'portal')) {

  ## Function -> auth_arcgis():
  # Authenticate to either ArcGIS Online (agol) or Portal (portal)
  # Allows for management of feature layers hosted on AGOL or Portal

  # auth_arcgis("agol"  )  # ArcGIS Online work
  # auth_arcgis("portal")  # Enterprise / services.sacog.org work

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



# Connect to Portal
auth_arcgis('portal')
token <- auth_code(host = Sys.getenv("ARCGIS_HOST"))
set_arc_token(token)
message("Authenticated against: ", Sys.getenv("ARCGIS_HOST"))



## Marriage Status

id <- '485906206a544d4a8960c03ee3287d6f' # '7bca736d66694a3cb6648b2e2e9d53cf' or '485906206a544d4a8960c03ee3287d6f'?
fl_to_update <- arc_open(id)
sf_ms <- fl_to_update |> get_layer(8) |> arc_select()
sf_ms

df_ms <- read_excel(file.path(path_server, 'Pop_8 Tracts ACS5.xlsx'), sheet='Tracts')
df_ms <- df_ms |> subset(`Year` == ACS_year)
df_ms <- df_ms |> subset(`Variable` == 'Now married')


## Birth Rates

id <- '99689339d13e47d7b17cf39958c7d100' # '99689339d13e47d7b17cf39958c7d100' or 'c572a1273c814f6eadf1cf46b953c698'?  One is a feature service the other is a feature layer?
fl_to_update <- arc_open(id)
sf_br <- fl_to_update |> get_layer(1) |> arc_select()
sf_br


df_br <- read_excel(file.path(path_server, 'Pop_6 Tracts ACS5.xlsx'), sheet='Tracts')
df_br <- df_br |> subset(`Year` == ACS_year)

