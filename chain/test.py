import pytest
from functools import partial
from click.testing import CliRunner
import xarray as xr
import numpy as np
from xclim.testing.helpers import test_timeseries as tt
from chain import cli


@pytest.fixture
def tas_series():
    """Return mean temperature time series."""
    _tas_series = partial(tt, variable="tas")
    return _tas_series


def test_chain(tas_series, tmp_path):
    # Create input file
    tas = tas_series(np.ones(366) + 271.15, start="1/1/2000")
    tas = tas.expand_dims(dim={"lon": np.linspace(-80, -70, 10), "lat": np.linspace(40, 50, 10)},)
    tas.lon.attrs["standard_name"] = "longitude"
    tas.lat.attrs["standard_name"] = "latitude"
    ds = xr.Dataset(data_vars={"tas": tas})
    
    input_file = tmp_path / "in.nc"
    ds.to_netcdf(input_file, engine="h5netcdf")

    output_file = tmp_path / "out.nc"
    args = [str(input_file), 
            str(output_file),
            "subset", 
            "-p", "small_geojson.json",
            "hdd", 
            "--thresh", "17 degC"]
    runner = CliRunner()
    results = runner.invoke(cli, args)
    
    assert results.exit_code == 0

    if output_file.exists():
        print(output_file)
        out = xr.open_dataset(str(output_file), engine="h5netcdf")
        outvar = list(out.data_vars.values())[0]
        np.testing.assert_allclose(outvar[0], 6588.0)
    else:
        raise FileNotFoundError