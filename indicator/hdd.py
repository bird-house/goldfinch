import click
import warnings
import xclim.cli

try:
    from dask.distributed import Client, distributed
except ImportError:
    pass

"""
# Notes

Based on xclim's CLI, which uses click.MultiCommand (recently deprecated in favor of click.Group). 

Click 

Dask-related options are copied from xclim but have not been tested and 
would require adding dependencies to the environment.

The only netCDF engine installed in the environment is h5netcdf, so the option to switch 
to another engine would not work in this env. 

The CLI's input is a path to a file, not a catalog item ID. There's a TODO below about this.

The CLI's output is a user input. We'll probably want to change this to a default output path.
"""

class Cli(click.MultiCommand):
    """Main cli class."""

    def list_commands(self, ctx):
        """Return the available commands (other than the indicators)."""
        return (
            "heating_degree_days",
        )

    def get_command(self, ctx, cmd_name):
        """Return the requested command."""
        if cmd_name in self.list_commands(ctx):
            command = xclim.cli._create_command(cmd_name)
        return command


@click.command(
    cls=Cli,
    chain=True,
    help="Command line tool to compute indices on netCDF datasets. Indicators are referred to by their "
    "(case-insensitive) identifier, as in xclim.core.indicator.registry.",
    invoke_without_command=True,
)
@click.option(
    "-i",
    "--input",
    help="Input dataset identifier from catalog.",
    multiple=True,
)
@click.option("-o", "--output", help="Output filepath. A new file will be created")
@click.option(
    "-v", "--verbose", help="Print details about context and progress.", count=True
)
@click.option(
    "--dask-nthreads",
    type=int,
    help="Start a dask.distributed Client with this many threads and 1 worker. "
    "If not specified, the local scheduler is used. If specified, '--dask-maxmem' must also be given",
)
@click.option(
    "--dask-maxmem",
    help="Memory limit for the dask.distributed Client as a human readable string (ex: 4GB). "
    "If specified, '--dask-nthreads' must also be specified.",
)
@click.option(
    "--chunks",
    help="Chunks to use when opening the input dataset(s). "
    "Given as <dim1>:num,<dim2:num>. Ex: time:365,lat:168,lon:150.",
)
@click.option(
    "--engine",
    help="Engine to use when opening the input dataset(s). "
    "If not specified, xarray decides.",
)
@click.pass_context
def cli(ctx, **kwargs):
    """Entry point for the command line interface.

    Manages the global options.
    """
    if not kwargs["verbose"]:
        warnings.simplefilter("ignore", FutureWarning)
        warnings.simplefilter("ignore", DeprecationWarning)

    if len(kwargs["input"]) == 0:
        kwargs["input"] = None
    elif len(kwargs["input"]) == 1:
        # TODO: Map catalog ID to path or URL
        kwargs["input"] = kwargs["input"][0]

    if kwargs["dask_nthreads"] is not None:
        if not distributed:
            raise click.BadOptionUsage(
                "dask_nthreads",
                "Dask's distributed scheduler is not installed, only the "
                "local scheduler (non-customizable) can be used.",
                ctx,
            )
        if kwargs["dask_maxmem"] is None:
            raise click.BadOptionUsage(
                "dask_nthreads",
                "'--dask-maxmem' must be given if '--dask-nthreads' is given.",
                ctx,
            )

        client = Client(
            n_workers=1,
            threads_per_worker=kwargs["dask_nthreads"],
            memory_limit=kwargs["dask_maxmem"],
        )
        click.echo(
            "Dask client started. The dashboard is available at http://127.0.0.1:"
            f"{client.scheduler_info()['services']['dashboard']}/status"
        )
    if kwargs["chunks"] is not None:
        kwargs["chunks"] = {
            dim: int(num)
            for dim, num in map(lambda x: x.split(":"), kwargs["chunks"].split(","))
        }

    kwargs["xr_kwargs"] = {
        "chunks": kwargs["chunks"] or {},
    }
    ctx.obj = kwargs

cli.result_callback()(click.pass_context(xclim.cli.write_file))


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter
