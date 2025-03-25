
SET NOCOUNT ON;


DECLARE @FFprdStart INT SET @FFprdStart = 20 --free-flow period starts at or after this time at night
DECLARE @FFprdEnd INT SET @FFprdEnd = 6 --free-flow period ends before this time in the morning

--list of weekdays
DECLARE @weekdays TABLE (day_name VARCHAR(9))
	INSERT INTO @weekdays VALUES ('Monday')
	INSERT INTO @weekdays VALUES ('Tuesday')
	INSERT INTO @weekdays VALUES ('Wednesday')
	INSERT INTO @weekdays VALUES ('Thursday')
	INSERT INTO @weekdays VALUES ('Friday')

--Get TMC-level free-flow speed for each year


--get free-flow speed, based on 8p-6a speed, for all available months of year
SELECT
	DISTINCT tmc.tmc,
	tmc.f_system,
	tmc.nhs,
	CASE WHEN f_system IN (1,2)
		THEN PERCENTILE_CONT(0.85)
			WITHIN GROUP (ORDER BY speed)
			OVER (PARTITION BY tmc_code)
		ELSE PERCENTILE_CONT(0.6)
			WITHIN GROUP (ORDER BY speed)
			OVER (PARTITION BY tmc_code)
		END AS ff_speed_art60thp --85th percentile speed for freeways; 60th percentile for arterials
-- INTO #ff_spd_tbl
FROM npmrds_2023_alltmc_txt tmc
	LEFT JOIN npmrds_2023_alltmc_paxtruck_comb tt
		ON tmc.tmc = tt.tmc_code
WHERE (DATEPART(hh,measurement_tstamp) >= @FFprdStart
		OR DATEPART(hh,measurement_tstamp) < @FFprdEnd)
		AND ((tmc.nhs = 1) OR (tmc.nhs = 2 AND f_system IN (1,2))) --on NHS only
