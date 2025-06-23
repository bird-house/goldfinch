import pytest
from functools import partial
from click.testing import CliRunner
import xarray as xr
import numpy as np
from xclim.testing.helpers import test_timeseries as tt
from hdd import cli


@pytest.fixture
def tas_series():
    """Return mean temperature time series."""
    _tas_series = partial(tt, variable="tas")
    return _tas_series


def test_hdd(tas_series, tmp_path):
    # Create input file
    tas = tas_series(np.ones(366) + 271.15, start="1/1/2000")
    ds = xr.Dataset(data_vars={"tas": tas})
    input_file = tmp_path / "in.nc"
    output_file = tmp_path / "out.nc"

    ds.to_netcdf(input_file, engine="h5netcdf")

    args = ["-i", str(input_file), "-o", str(output_file), "-v", "heating_degree_days"]
    runner = CliRunner()
    results = runner.invoke(cli, args)
    assert "Processing :" in results.output

    out = xr.open_dataset(output_file)
    outvar = list(out.data_vars.values())[0]
    np.testing.assert_allclose(outvar[0], 6588.0)
