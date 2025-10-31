import click
import clisops.core
import geopandas as gpd
import xarray as xr
import xclim


"""
This CLI demonstrates a workflow where commands can be called individually
or chained together in memory. That is, each individual command accepts and
returns an xarray.Dataset. The `click.group` is responsible for readingin the
input data from disk, and writing the output data to disk.
"""


@click.group(chain=True, help="Chained CLI", invoke_without_command=True)
@click.argument("input", type=click.File("r"))
@click.argument("output")
def cli(input, output):
    pass

@cli.result_callback()
def process_pipeline(processors, input, output):
    """Read the input, execute commands in memory, write output to disk."""
    # Read the input data into an xarray.Dataset
    ds = xr.open_dataset(input.name, engine="h5netcdf")

    # Execute individual commands - not obvious here, but options are passed
    for processor in processors:
        ds = processor(ds)

    # Write output to disk
    ds.to_netcdf(output, engine="h5netcdf")


@cli.command
@click.option("-p", "--poly", help="Path to the polygon shapefile.")
@click.option("-s",
              "--start",
              help="""Start date for the subset. Can be year ("%Y"), year-month ("%Y-%m") or year-month-day (
              "%Y-%m-%d").""",
              default=None)
@click.option("-e", "--end", help="End date for the subset.", default=None)
def subset(**kwargs):
    """Subset on polygon"""
    def processor(ds):
        gdf = gpd.GeoDataFrame.from_file(kwargs["poly"])
        return clisops.core.subset_shape(ds=ds, 
                                         shape=gdf, 
                                         start_date=kwargs["start"], 
                                         end_date=kwargs["end"]
                                        )

    return processor


@cli.command
@click.option("--thresh", type=str)
def hdd(**kwargs):
    """Heating degree days"""
    def processor(ds):
        return xclim.atmos.heating_degree_days(ds["tas"], 
                                               thresh=kwargs["thresh"]
                                               )

    return processor


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter
