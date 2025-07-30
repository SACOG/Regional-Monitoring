



library(tidyverse)
library(here)
library(splitstackshape)

# Build peer table
ntdid <-
  c(
    90019,#sacrt and peers
    50027,
    80006,
    90026,
    00008,
    90013,
    90142, #unitrans and peers
    70019,
    30036,
    00047,
    50158,
    20145,
    90090, #YoloTD and peers
    90162,
    90159,
    50146,
    90089,
    90232,
    90061, #Yuba-Sutter Transit and peers
    90208,
    90233,
    90173,
    00057,
    90088,
    90216, #SCT Link and peers
    00065,
    40192,
    20176,
    91005,
    00363,
    90168, #Roseville Transit and peers
    90161,
    90131,
    00046,
    90159,
    90164,
    90196, #Placer County Transit and peers
    00011,
    50146,
    90017,
    90078,
    90159,
    90229, #El Dorado Transit and peers
    00046,
    90034,
    50157,
    90043,
    90161
  )

agency <-
  c(
    "Sacramento Regional Transit District",
    "Metro Transit",
    "Denver Regional Transportation District",
    "San Diego Metropolitan Transit System",
    "Tri-County Metropolitan Transportation District of Oregon",
    "Santa Clara Valley Transportation Authority",
    "University of California, Davis",
    "University of Iowa",
    "City of Charlottesville",
    "City of Corvallis",
    "University of Michigan Parking and Transportation Services",
    "Tompkins Consolidated Area Transit",
    "Yolo County Transportation District",
    "The Eastern Contra Costa Transit Authority",
    "Western Contra Costa Transit Authority",
    "Madison County Transit District",
    "County of Sonoma",
    "Solano County Transit",
    "Yuba-Sutter Transit Authority",
    "Butte County Association of Governments",
    "Yuma County Intergovernmental Public Transportation Authority",
    "Transit Joint Powers Authority for Merced County",
    "Central Oregon Intergovernmental Council",
    "Napa Valley Transportation Authority",
    "County of Sacramento Municipal Services Agency",
    "Benton County",
    "Martin County",
    "Kaser Bus Service",
    "Madera County",
    "Clackamas County",
    "City of Roseville",
    "City of Union City",
    "City of Scottsdale",
    "City of Wilsonville",
    "Western Contra Costa Transit Authority",
    "Ventura County Transportation Commission",
    "County of Placer",
    "Valley Regional Transit",
    "Madison County Transit District",
    "City of Santa Rosa",
    "Central Contra Costa Transit Authority",
    "Western Contra Costa Transit Authority",
    "El Dorado County Transit Authority",
    "City of Wilsonville",
    "City of Glendale",
    "Butler County Regional Transit Authority",
    "City of Commerce",
    "City of Union City"
  )

acronym <-
  c(
    "SacRT",
    "METRO",
    "RTD",
    "MTS",
    "Trimet",
    "VTA",
    "Unitrans",
    "CAMBUS",
    "CAT",
    "CTS",
    "UM",
    "TCAT",
    "YoloTD",
    "ECCTA",
    "WestCAT",
    "MCT",
    "SCT",
    "SolTrans",
    "YST",
    "B-Line",
    "YCAT",
    "TheBus",
    "CET",
    "NVTA",
    "SCTLink",
    "BAT",
    "MARTY",
    "Kaser",
    "MCC",
    "ClackCo",
    "Roseville Transit",
    "UCT",
    "Scottsdale Trolley",
    "SMART",
    "WestCAT",
    "VCTC",
    "PCT",
    "VRT",
    "MCT",
    "CityBus",
    "CCCTA",
    "WestCAT",
    "EDT",
    "SMART",
    "Beeline",
    "BCRTA",
    "Commerce Transit",
    "UCT"
  )

peer_assign <-
  c(
    "self",
    "sacrt_peer",
    "sacrt_peer",
    "sacrt_peer",
    "sacrt_peer",
    "sacrt_peer",
    "self",
    "unitrans_peer",
    "unitrans_peer",
    "unitrans_peer",
    "unitrans_peer",
    "unitrans_peer",
    "self",
    "yolotd_peer",
    "yolotd_peer",
    "yolotd_peer",
    "yolotd_peer",
    "yolotd_peer",
    "self",
    "ysta_peer",
    "ysta_peer",
    "ysta_peer",
    "ysta_peer",
    "ysta_peer",
    "self",
    "sctlink_peer",
    "sctlink_peer",
    "sctlink_peer",
    "sctlink_peer",
    "sctlink_peer",
    "self",
    "roseville_peer",
    "roseville_peer",
    "roseville_peer",
    "roseville_peer",
    "roseville_peer",
    "self",
    "pct_peer",
    "pct_peer",
    "pct_peer",
    "pct_peer",
    "pct_peer",
    "self",
    "edt_peer",
    "edt_peer",
    "edt_peer",
    "edt_peer",
    "edt_peer"
  )

peer_table <- tibble(ntdid, agency, acronym, peer_assign)



## TODO:  What does this chunk of code do?  I don't see a "mode" field

# # match RTA defined modes with NTD mode codes
# 
# ntd_modes_map <- c(
#   light_rail = "LR",
#   urban_bus = "MB",
#   commuter_bus = "CB",
#   demand_response = "DR"
# )
# 
# peer_table$ntd_mode <- NA
# 
# for (i in 1:nrow(peer_table)) {
#   x = as.character(peer_table$mode[i]) # TODO: Where does mode come from?
#   peer_table$ntd_mode[i] <- ntd_modes_map[x]
# }



# export clean peer table
write_csv(peer_table, here("tables", "peer_table.csv"))


