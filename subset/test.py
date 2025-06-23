import pytest
from functools import partial
from click.testing import CliRunner
import xarray as xr
import numpy as np
from xclim.testing.helpers import test_timeseries
from poly_subset import cli


@pytest.fixture
def tas_series():
    """Return mean temperature time series."""
    _tas_series = partial(test_timeseries, variable="tas")
    return _tas_series


def test_poly_subset(tas_series, tmp_path):
    # Create input file
    tas = tas_series(np.ones(366) + 271.15, start="1/1/2000")
    tas = tas.expand_dims(dim={"lon": np.linspace(-80, -70, 10), "lat": np.linspace(40, 50, 10)},)
    tas.lon.attrs["standard_name"] = "longitude"
    tas.lat.attrs["standard_name"] = "latitude"

    ds = xr.Dataset(data_vars={"tas": tas})
    input_file = tmp_path / "in.nc"
    output_file = tmp_path / "out.nc"

    ds.to_netcdf(input_file, engine="h5netcdf")

    args = ["-i", str(input_file),
            "-o", str(output_file),
            "-p", "small_geojson.json",
            "-b", ".1",
            "-s", "2000-06",
            "-e", "2000-08",]
    runner = CliRunner()
    result = runner.invoke(cli, args)
    assert not result.exception

    out = xr.open_dataset(output_file)
    assert "tas" in out.data_vars
    assert out.time.isel(time=0) == np.datetime64("2000-06-01T00:00:00")
    assert out.time.isel(time=-1) == np.datetime64("2000-08-31T00:00:00")
    assert len(out.tas.lon) == 1
    assert len(out.tas.lat) == 1

