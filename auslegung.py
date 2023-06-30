"""
This script is used to find the optimal parameters for the scaling of a battery storage
The household data is taken from the [*Standard Battery Application Profiles (SBAP) paper*](https://doi.org/10.1016/j.est.2019.101077)
"""

import pandas as pd
from tqdm import tqdm


def electricity_costs(grid_profile, electricity_price, feedin_tariff):
    grid_sell = (
        grid_profile.loc[grid_profile < 0].sum() * 0.25 * feedin_tariff * -1
    )  # negative sign
    grid_buy = grid_profile.loc[grid_profile > 0].sum() * 0.25 * electricity_price
    return grid_buy - grid_sell


def self_consumption(grid_profile, pv_profile):
    feedin = grid_profile[grid_profile < 0].sum() * -1
    pv = pv_profile.sum()
    return 1 - (feedin / pv)


def self_sufficiency(grid_profile, load_profile):
    gridbuy = grid_profile[grid_profile > 0].sum()
    load = load_profile.sum()
    return 1 - (gridbuy / load)


def print_results(
    results,
    simulation,
    total_demand,
    total_generation,
    capacity,
    max_power_charging,
    max_power_discharging,
    costs,
    ssr,
    scr,
):
    print("Simulation: " + simulation)
    print(f"Total demand:      {total_demand:.0f} kWh")
    print(f"Total generation:  {total_generation:.0f} kWh")
    print(f"Capacity:          {capacity:.3f} kWh")
    print(f"Max Power Charging:{max_power_charging:.3f} kW")
    print(f"Max Power Discharging: {max_power_discharging:.3f} kW")
    print(f"Electricity costs:  {costs:.2f} €")
    print(f"Self-sufficiency:   {ssr*100:.2f} %")
    print(f"Self-consumption:   {scr*100:.2f} %")
    results.loc[len(results)] = {
        "simulation": simulation,
        "total_demand": total_demand,
        "total_generation": total_generation,
        "capacity": capacity,
        "max_power_charging": max_power_charging,
        "max_power_discharging": max_power_discharging,
        "costs": costs,
        "ssr": ssr,
        "scr": scr,
    }


def greedy_strategy(
    profile,
    capacity,
    max_power_charge,
    max_power_discharge,
    eff_charge,
    eff_discharge,
    initial_soc,
    dt,
):
    df = profile.copy()  # make a new copy of the dataframe
    # add new empty columns to the dataframe
    df["grid"] = 0.0  # grid power in kW
    df["power"] = 0.0  # battery power in kW
    df["soc"] = 0.0  # battery SOC in p.u.

    soc = initial_soc

    for time, residual in profile["residual"].items():
        if residual < 0:
            # charge
            power = min(abs(residual), max_power_charge)
            soc_new = min(soc + (power * dt * eff_charge) / capacity, 1.0)
            power_real = -(soc_new - soc) * capacity / dt * (1 / eff_charge)
        else:
            # discharge
            power = min(abs(residual), max_power_discharge)
            soc_new = max(soc - (power * dt * (1 / eff_discharge)) / capacity, 0.0)
            power_real = -(soc_new - soc) * capacity / dt * eff_discharge

        grid = residual - power_real
        soc = soc_new

        df.loc[time, "grid"] = grid
        df.loc[time, "power"] = power_real
        df.loc[time, "soc"] = soc

    return df


if __name__ == "__main__":

    pd.options.plotting.backend = "plotly"
    template = "plotly_white"

    electricity_price = 0.40
    feedin_tariff = 0.00
    eff_charge = 0.85
    eff_discharge = 0.8

    """notrun
    name = "Simulation1"
    max_power_charge = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
    max_power_discharge = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
    capacity = [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5, 3]
    """

    """processed
    name = "Simulation2"
    max_power_charge = [0.4, 0.5, 0.6, 0.7]
    max_power_discharge = [0.1, 0.2, 0.3, 0.4]
    capacity = [0.9, 1, 1.1, 1.2]
    """

    """processed
    name = "Simulation3"
    max_power_charge = [0.6]
    max_power_discharge = [0.3]
    capacity = [0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4]
    """
    
    """processed
    name = "Simulation4"
    max_power_charge = [0.4, 0.5, 0.6, 0.7, 0.8]
    max_power_discharge = [0.4, 0.5, 0.6, 0.7, 0.8]
    capacity = [0.75, 1, 1.25, 1.5]
    """
    
    """processed
    name = "Simulation5"
    max_power_charge = [0.4, 0.5, 0.6, 0.7, 0.8]
    max_power_discharge = [0.1, 0.2, 0.3, 0.4, 0.5]
    capacity = [1.5]
    """
    
    """processed
    name = "Simulation6"
    max_power_charge = [0.5, 0.6, 0.7, 0.8]
    max_power_discharge = [0.2, 0.3, 0.4, 0.5]
    capacity = [1.5]
    """

    initial_soc = 0.5
    dt = 0.25

    # Original data
    profile = pd.read_csv("./data/household_profile.csv", index_col=0, parse_dates=True)
    # profile.plot(template=template, labels={"value": "Power [kW]"})

    # Data for 600 Wp PV and 2 Person household
    profile["pv"] = profile["pv"] / 8
    profile["load"] = profile["load"] / 2
    # profile.plot(template=template, labels={"value": "Power [kW]"})

    profile["residual"] = profile["load"] - profile["pv"]
    # profile["residual"].plot(template=template, labels={"value": "Power [kW]"})

    simulation = "Without Storage"

    # demand/consumption
    total_demand = profile["load"].sum() * dt
    total_generation = profile["pv"].sum() * dt

    # electricity costs
    costs = electricity_costs(profile["residual"], electricity_price, feedin_tariff)

    # self-consumption / self-sufficiency
    ssr = self_sufficiency(profile["residual"], profile["load"])
    scr = self_consumption(profile["residual"], profile["pv"])

    results = pd.DataFrame(
        columns=[
            "simulation",
            "total_demand",
            "total_generation",
            "capacity",
            "max_power_charging",
            "max_power_discharging",
            "costs",
            "ssr",
            "scr",
        ]
    )

    print_results(
        results=results,
        simulation=simulation,
        total_demand=total_demand,
        total_generation=total_generation,
        capacity=0,
        max_power_charging=0,
        max_power_discharging=0,
        costs=costs,
        ssr=ssr,
        scr=scr,
    )

    with tqdm(
        total=len(capacity) * len(max_power_charge) * len(max_power_discharge)
    ) as pbar:

        for x in capacity:
            for y in max_power_charge:
                for z in max_power_discharge:

                    df_greedy = greedy_strategy(
                        profile,
                        x,
                        y,
                        z,
                        eff_charge,
                        eff_discharge,
                        initial_soc,
                        dt,
                    )
                    # df_greedy[["residual", "power"]].plot(template=template, labels={"value": "Power [kW]"})
                    # df_greedy["soc"].plot(template=template, labels={"value": "SOC"})

                    costs = electricity_costs(
                        df_greedy["grid"], electricity_price, feedin_tariff
                    )
                    ssr = self_sufficiency(df_greedy["grid"], df_greedy["load"])
                    scr = self_consumption(df_greedy["grid"], df_greedy["pv"])

                    simulation = "Greedy"

                    print_results(
                        results,
                        simulation,
                        total_demand,
                        total_generation,
                        x,
                        y,
                        z,
                        costs,
                        ssr,
                        scr,
                    )
                    pbar.update(1)
                    print("\n")

    results.to_csv("./results/auslegung/auslegung" + name + ".csv")

    print(results)
