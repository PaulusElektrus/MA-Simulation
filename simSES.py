# https://gitlab.lrz.de/open-ees-ses/simses

import os
from simses.main import SimSES
from configparser import ConfigParser

# Battery
power = 600  # W
capacity = 1000  # Wh

# Household
electricity_consumption = 2e6  # Wh/a
pv_installed_capacity = 600  # Wp

# Costs & Other
loop_years = 1  # a
investment_costs = 600  # €
electricity_price = 0.40  # €/kWh
pv_feedin_tariff = 0.0  # €/kWh
discount_rate = 0.02

sim_params = f"""
[GENERAL]
START = 2014-01-01 00:00:00
END = 2014-12-31 23:59:59
TIME_STEP = 3600
LOOP = {loop_years}

[ENERGY_MANAGEMENT]
STRATEGY = ResidentialPvGreedy

[BATTERY]
START_SOC = 0.5
MIN_SOC = 0
MAX_SOC = 1

[STORAGE_SYSTEM]
; Configuration of the AC storage system:
; Format: AC-system name, max AC power in W, DC voltage level in V, ACDC converter name, housing name, HVAC name
STORAGE_SYSTEM_AC =
    system_1,{power},43,notton,no_housing,no_hvac

; Configuration of the AC/DC converter:
; Format: ACDC converter name, converter type, optional: number of converters
ACDC_CONVERTER =
    notton,NottonAcDcConverter

; Configuration of the DC storage system. Every AC system must have at least 1 DC system
; Format: AC-system name, DCDC converter name, storage technology name
STORAGE_SYSTEM_DC =
   system_1,no_loss,nmc

; Configuration of the DCDC converter
; Format: DCDC converter name, converter type, [efficiency]
DCDC_CONVERTER =
    no_loss,NoLossDcDcConverter

; Configuration of the storage technology.
; Format: storage technology name, energy in Wh, technology type, [technology specific parameters]
STORAGE_TECHNOLOGY =
    nmc,{capacity},lithium_ion,GenericCell

[PROFILE]
POWER_PROFILE_DIR = {os.path.abspath("./data")}
LOAD_PROFILE = simses_load_profile
GENERATION_PROFILE = simses_pv_profile

LOAD_SCALING_FACTOR = {electricity_consumption}
GENERATION_SCALING_FACTOR = {pv_installed_capacity}
"""

analysis_params = f"""
[ECONOMIC_ANALYSIS]

INVESTMENT_COSTS = {investment_costs}
USE_SPECIFIC_COSTS = False

ELECTRICITY_PRICE = {electricity_price}
PV_FEED_IN_TARIFF = {pv_feedin_tariff}

DISCOUNT_RATE = {discount_rate}
"""

sim_config = ConfigParser()
sim_config.read_string(sim_params)

analysis_config = ConfigParser()
analysis_config.read_string(analysis_params)

path = os.path.abspath(".")
result_path = os.path.join(path, "results").replace("\\", "/") + "/"


if __name__ == "__main__":

    simses = SimSES(
        path=result_path,
        name="greedy",
        simulation_config=sim_config,
        analysis_config=analysis_config,
    )
    simses.run()
