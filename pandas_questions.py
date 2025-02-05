"""Plotting referendum results in pandas.

In short, we want to make beautiful map to report results of a referendum. In
some way, we would like to depict results with something similar to the maps
that you can find here:
https://github.com/x-datascience-datacamp/datacamp-assignment-pandas/blob/main/example_map.png

To do that, you will load the data as pandas.DataFrame, merge the info and
aggregate them by regions and finally plot them on a map using `geopandas`.
"""
import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt


def load_data():
    """Load data from the CSV files referundum/regions/departments."""
    path = "data"
    referendum = pd.read_csv(f"{path}/referendum.csv",
                             delimiter=';',
                             on_bad_lines='skip')
    regions = pd.read_csv(f"{path}/regions.csv",
                          on_bad_lines='skip')
    departments = pd.read_csv(f"{path}/departments.csv",
                              delimiter=',',
                              on_bad_lines='skip')

    return referendum, regions, departments


def merge_regions_and_departments(regions: pd.DataFrame,
                                  departments: pd.DataFrame):
    """Merge regions and departments in one DataFrame.

    The columns in the final DataFrame should be:
    ['code_reg', 'name_reg', 'code_dep', 'name_dep']
    """
    regions.columns = ['id', 'code_reg', 'name_reg', 'slug']
    departments.columns = ['id', 'code_reg', 'code_dep', 'name_dep', 'slug']
    merged_reg_dep = pd.merge(regions[['code_reg', 'name_reg']],
                              departments[['code_reg', 'code_dep',
                                           'name_dep']],
                              on='code_reg',
                              how='left')

    return merged_reg_dep


def merge_referendum_and_areas(referendum: pd.DataFrame,
                               regions_and_departments: pd.DataFrame):
    """Merge referendum and regions_and_departments in one DataFrame.

    You can drop the lines relative to DOM-TOM-COM departments, and the
    french living abroad.
    """
    # Add a code_dep column to referendum and keep only the numeric ones
    referendum["code_dep"] = referendum["Department code"]
    referendum = referendum[((referendum["code_dep"].str.isnumeric()) |
                            (referendum["code_dep"].isin(["2A", "2B"])))]

    # Remove lines : on reg_dep, separate corsica from the rest
    corsica = regions_and_departments[(
        regions_and_departments["code_dep"].isin(["2A", "2B"])
        )]
    not_corsica = regions_and_departments[(
        ~regions_and_departments["code_dep"].isin(["2A", "2B"])
        )]

    # Remove DOMTOM and set as int and back to str to
    # have 1 as "1" and not "01" for ex
    not_corsica = not_corsica[not_corsica["code_dep"].astype('int') < 100]
    not_corsica["code_dep"] = not_corsica["code_dep"].astype('int')
    not_corsica["code_dep"] = not_corsica["code_dep"].astype('str')

    # Reconcatenate the two
    regions_and_departments = pd.concat([not_corsica, corsica], axis=0)

    # Now merge
    merged_ref_reg_dep = pd.merge(referendum, regions_and_departments,
                                  on='code_dep', how='left')

    return merged_ref_reg_dep


def compute_referendum_result_by_regions(referendum_and_areas: pd.DataFrame):
    """Return a table with the absolute count for each region.

    The return DataFrame should be indexed by `code_reg` and have columns:
    ['name_reg', 'Registered', 'Abstentions', 'Null', 'Choice A', 'Choice B']
    """
    abs_count = (
        referendum_and_areas
        .groupby(["code_reg", "name_reg"])
        .aggregate(np.sum)
        .reset_index()
    )

    return abs_count[['name_reg', 'Registered', 'Abstentions',
                      'Null', 'Choice A', 'Choice B']]


def plot_referendum_map(referendum_result_by_regions: pd.DataFrame):
    """Plot a map with the results from the referendum.

    * Load the geographic data with geopandas from `regions.geojson`.
    * Merge these info into `referendum_result_by_regions`.
    * Use the method `GeoDataFrame.plot` to display the result map. The results
      should display the rate of 'Choice A' over all expressed ballots.
    * Return a gpd.GeoDataFrame with a column 'ratio' containing the results.
    """
    reg_json = gpd.read_file("data/regions.geojson")
    referendum_result_by_regions['nom'] = (
        referendum_result_by_regions['name_reg']
    )
    referendum_result_by_regions["ratio"] = (
        referendum_result_by_regions["Choice A"] /
        (referendum_result_by_regions["Choice A"] +
         referendum_result_by_regions["Choice B"])
    )
    to_plot = gpd.GeoDataFrame(pd.merge(referendum_result_by_regions,
                               reg_json, on='nom'))
    to_plot.plot("ratio")
    return to_plot


if __name__ == "__main__":

    referendum, df_reg, df_dep = load_data()
    regions_and_departments = merge_regions_and_departments(
        df_reg, df_dep
    )
    referendum_and_areas = merge_referendum_and_areas(
        referendum, regions_and_departments
    )
    referendum_results = compute_referendum_result_by_regions(
        referendum_and_areas
    )
    print(referendum_results)

    plot_referendum_map(referendum_results)
    plt.show()
