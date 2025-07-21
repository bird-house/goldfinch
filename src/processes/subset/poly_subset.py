import click
import clisops.core
import warnings
import geopandas as gpd
import xarray as xr

"""
# Notes

This is a basic implementation of a clisops command. 

There is potential to use the click.Group command to chain multiple commands together, 
but this one here is standalone.  

Missing features:
 - error handling; 
 - multiple input datasets; 
 - dask parallelism;
 - input from catalog (currently only accepts a file path);
 - CRS option; 
 - xarray engine option; 
"""


@click.command()
@click.option(
    "-i",
    "--input",
    help="Input dataset identifier from catalog.",
    multiple=False,
)
@click.option("-o", "--output", help="Output filepath. A new file will be created")
@click.option("-p", "--poly", help="Path to the polygon shapefile.")
@click.option("-b", "--buffer",
              help="Buffer distance to apply to the polygon. Units are the same as the coordinate system of the polygon.",
              default=0, type=float)
@click.option("-s",
              "--start",
              help="""Start date for the subset. Can be year ("%Y"), year-month ("%Y-%m") or year-month-day (
              "%Y-%m-%d").""",
              default=None)
@click.option("-e", "--end", help="End date for the subset.", default=None)
@click.option("-f", "--first_level", help="First level of the variable to subset.", default=None)
@click.option("-l", "--last_level", help="Last level of the variable to subset.", default=None)
@click.option(
    "-v", "--verbose", help="Print details about context and progress.", count=True
)
def cli(**kwargs):
    """Entry point for the command line interface.

    Manages the global options.
    """
    # if not kwargs["verbose"]:
    #     warnings.simplefilter("ignore", FutureWarning)
    #     warnings.simplefilter("ignore", DeprecationWarning)

    dsin = xr.open_dataset(kwargs["input"], engine="h5netcdf")
    gdf = gpd.GeoDataFrame.from_file(kwargs["poly"])
    buffer = kwargs["buffer"]
    out = clisops.core.subset_shape(ds=dsin, shape=gdf, buffer=buffer, start_date=kwargs["start"], end_date=kwargs[
        "end"],
                              first_level=kwargs["first_level"], last_level=kwargs["last_level"])

    out.to_netcdf(kwargs["output"], engine="h5netcdf")


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter
