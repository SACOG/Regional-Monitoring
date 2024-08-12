library(data.table)
library(openxlsx)
library(tidyverse)

clear <- function() {
  shell("cls")
}
setwd(paste0(getwd(), "/BEA"))

`%notin%` <- Negate(`%in%`)
sacog <- c("Yuba City", "Sacramento-Roseville-Folsom")
mtc <- c("San Francisco-Oakland-Berkeley", "Santa Rosa-Petaluma",
         "Vallejo", "Napa", "San Jose-Sunnyvale-Santa Clara")
scag <- c("Los Angeles-Long Beach-Anaheim",
          "Riverside-San Bernardino-Ontario",
          "Oxnard-Thousand Oaks-Ventura",
          "El Centro")

rdp <- read_csv("BEAbyIndustry.csv", skip = 3, na = "(D)") %>%
  filter(LineCode < 87) %>%
  select(c(GeoName, Level:`2022`)) %>%
  filter(!is.na(GeoName)) %>%
  filter(Description != "Addenda:") %>%
  mutate(GeoName = str_replace_all(GeoName, "\\(.*", "")) %>%
  mutate(GeoName = str_replace_all(GeoName, ",.*", "")) %>%
  mutate(MPO = ifelse(GeoName %in% sacog, "SACOG",
                      ifelse(GeoName %in% mtc, "MTC",
                             ifelse(GeoName %in% scag, "SCAG",
                                    ifelse(GeoName == "San Diego-Chula Vista-Carlsbad", "SANDAG", #nolint
                                           GeoName))))) %>%
  mutate(MPO = str_replace_all(MPO, "-.*", ""))

setDT(rdp)
rdp <- setcolorder(rdp, c("GeoName", "MPO", "Level", "Description"))
colnames(rdp) <- c("MSA", "MPO", "Level", "Industry", 2017:2022)
rdp_mpo <- rdp[, lapply(.SD, sum),
               by = c("MPO", "Industry", "Level"), .SDcols = `2017`:`2022`]
sacog <- rdp_mpo %>%
  filter(MPO == "SACOG")
ca_peers <- rdp_mpo %>%
  filter(MPO %in% c("MTC", "SANDAG", "SCAG"))
other_peers <- rdp_mpo %>%
  filter(MPO %notin% c("MTC", "SANDAG", "SCAG", "SACOG"))

# Excel set-up =================================================================
sheets <- list("SACOG GRP" = sacog,
               "CA MPO GRP" = ca_peers,
               "Peer MPO GRP" = other_peers,
               "MSA GRP" = rdp)
write.xlsx(sheets, "Output_1.xlsx")

# csv set-up ===================================================================
sacog$MSA <- "SACOG Total"
ca_peers$MSA <- paste(ca_peers$MPO, "Total")
sacog <- setcolorder(sacog, c("MSA", "MPO", "Level", "Industry"))
ca_peers <- setcolorder(ca_peers, c("MSA", "MPO", "Level", "Industry"))
rdp <- rbind(rdp, sacog, ca_peers)
rdp <- rdp %>%
  arrange(MPO, MSA) %>%
  pivot_longer(`2017`:`2022`, names_to = "Year", values_to = "GRP")

setDT(rdp)
rdp <- setcolorder(rdp, "Year")
rdp <- arrange(rdp, Year, MPO, MSA)
write.csv(rdp, "Output_1.csv")
