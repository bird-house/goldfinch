import pytest
from functools import partial
from click.testing import CliRunner
import xarray as xr
import numpy as np
from xclim.testing.helpers import test_timeseries as tt
from chain import cli


@pytest.fixture(scope="module")
def tas_series():
    """Return mean temperature time series."""
    _tas_series = partial(tt, variable="tas")
    return _tas_series


@pytest.fixture(scope="module")
def input_file(tas_series, tmpdir_factory):
    # Create input file
    input_file = str(tmpdir_factory.mktemp("input").join("in.nc"))
    tas = tas_series(np.ones(366) + 271.15, start="1/1/2000")
    tas = tas.expand_dims(dim={"lon": np.linspace(-80, -70, 10), "lat": np.linspace(40, 50, 10)},)
    tas.lon.attrs["standard_name"] = "longitude"
    tas.lat.attrs["standard_name"] = "latitude"
    ds = xr.Dataset(data_vars={"tas": tas})
    ds.to_netcdf(input_file, engine="h5netcdf")
    return input_file


def test_chain(input_file, tmp_path):
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
        out = xr.open_dataset(str(output_file), engine="h5netcdf")
        outvar = list(out.data_vars.values())[0]
        np.testing.assert_allclose(outvar[0], 6588.0)
    else:
        raise FileNotFoundError
    

def test_hdd(input_file, tmp_path):    
    output_file = tmp_path / "out.nc"
    args = [str(input_file), 
            str(output_file),
            "hdd", 
            "--thresh", "17 degC"]
    runner = CliRunner()
    results = runner.invoke(cli, args)
    
    assert results.exit_code == 0

    if output_file.exists():
        out = xr.open_dataset(str(output_file), engine="h5netcdf")
        outvar = list(out.data_vars.values())[0]
        np.testing.assert_allclose(outvar[0], 6588.0)
    else:
        raise FileNotFoundError
    

def test_subset(input_file, tmp_path):
    output_file = tmp_path / "out.nc"
    args = [str(input_file), 
            str(output_file),
            "subset", 
            "-p", "small_geojson.json",
            "-s", "2000-06",
            "-e", "2000-08",]
    runner = CliRunner()
    results = runner.invoke(cli, args)
    
    assert results.exit_code == 0

    if output_file.exists():
        out = xr.open_dataset(str(output_file), engine="h5netcdf")
        assert "tas" in out.data_vars
        assert out.time.isel(time=0) == np.datetime64("2000-06-01T00:00:00")
        assert out.time.isel(time=-1) == np.datetime64("2000-08-31T00:00:00")
        assert len(out.tas.lon) == 1
        assert len(out.tas.lat) == 1
    else:
        raise FileNotFoundError
    