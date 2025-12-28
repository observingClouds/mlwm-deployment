#!/leonardo/home/userexternal/hschulz0/repos/mlwm-deployment/.pixi/envs/default/bin/python
#SBATCH --job-name=regrid
#SBATCH --output=regrid.log
#SBATCH --error=regrid.log
#SBATCH --time=00:30:00
#SBATCH --mem=60GB
#SBATCH --exclusive
#SBATCH -p boost_usr_prod
#SBATCH -n 2
#SBATCH --qos=boost_qos_dbg

import xesmf as xe
import xarray as xr
import os
from pyproj import Proj
import tqdm

sets = {
    "sfc_boundary": {
        "data": "/leonardo_scratch/large/userexternal/hschulz0/data/mars_request/globalDT/zarr/globalDT_regridded_20250624_sif_sf.zarr",
        "target_grid": "grids/era_7deg_model1_config.latlon.nc",
        "weights_file": "bilinear_weights_era_7deg_surface.nc",
        "output_path": "sf_era_7deg_boundary_regridded.zarr"
    },
    "sfc_interior": {
        "data": "/leonardo_scratch/large/userexternal/hschulz0/data/mars_request/globalDT/zarr/globalDT_regridded_20250624_sif_sf.zarr",
        "target_grid": "grids/danra_model1_config.latlon.nc",
        "weights_file": "bilinear_weights_danra_surface.nc",
        "output_path": "sf_danra_interior_regridded.zarr"
    },
    "pressure_boundary": {
        "data": "/leonardo_scratch/large/userexternal/hschulz0/data/mars_request/globalDT/zarr/globalDT_regridded_20250624_sif_pl.zarr",
        "target_grid": "grids/era_7deg_model1_config.latlon.nc",
        "weights_file": "bilinear_weights_era_7deg_pressure.nc",
        "output_path": "pl_era_7deg_boundary_regridded.zarr"
    },
    "pressure_interior": {
        "data": "/leonardo_scratch/large/userexternal/hschulz0/data/mars_request/globalDT/zarr/globalDT_regridded_20250624_sif_pl.zarr",
        "target_grid": "grids/danra_model1_config.latlon.nc",
        "weights_file": "bilinear_weights_danra_pressure.nc",
        "output_path": "pl_danra_interior_regridded.zarr"
}
}

for setup, setup_dict in tqdm.tqdm(sets.items()):
    data = xr.open_zarr(setup_dict["data"])
    ds_w_target_grid = xr.open_dataset(setup_dict["target_grid"])
    if not "x" in ds_w_target_grid:
        proj = Proj(proj="eqc", lon_0=0, datum="WGS84")
        x,y = proj(ds_w_target_grid.longitude, ds_w_target_grid.latitude)
        ds_w_target_grid['x'] = (("grid_index"), x)
        ds_w_target_grid['y'] = (("grid_index"), y)
    weights_file = setup_dict["weights_file"]
    output_path = setup_dict["output_path"]

    if os.path.exists(weights_file):
        regridder = xe.Regridder(data, ds_w_target_grid, "nearest_d2s", reuse_weights=True, weights=weights_file)
    else:
        regridder = xe.Regridder(data, ds_w_target_grid, "nearest_d2s")
        regridder.to_netcdf(weights_file)
    
    ds_out = regridder(data, keep_attrs=True)
    if "latitude" in ds_out and "longitude" in ds_out:
        ds_out = ds_out.rename({"latitude": "lat", "longitude": "lon"})
    ds_out.to_zarr(output_path, mode="w", consolidated=True)