"""
Script to regrid datasets like globalDT to grids used during model training.
"""

import xesmf as xe
import xarray as xr
import os
import argparse


def regrid(data, ds_w_target_grid, weights_file):
    """Regrid the input data to the target grid using xesmf.

    Parameters:
    - data: xarray Dataset to be regridded.
    - ds_w_target_grid: xarray Dataset representing the target grid.
    - weights_file: Path to the weights file for regridding.

    Returns:
    - Regridded xarray Dataset.
    """
    if os.path.exists(weights_file):
        regridder = xe.Regridder(data, ds_w_target_grid, "bilinear", reuse_weights=True, weights=weights_file)
    else:
        regridder = xe.Regridder(data, ds_w_target_grid, "bilinear")
        regridder.to_netcdf(weights_file)
    
    return regridder(data, keep_attrs=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Regrid datasets using xesmf.")
    parser.add_argument("--input-path", type=str, required=True, help="Path to the input zarr dataset.")
    parser.add_argument("--weights-file", type=str, default="bilinear_weights.nc", help="Path to the weights file. Will be created if it does not exist.")
    parser.add_argument("--output-path", type=str, default="regridded_data.zarr", help="Path to the output zarr directory.")
    parser.add_argument("--target-dataset", type=str, default="s3://danra/v0.5.0/single_levels.zarr/", help="Path to the target dataset for regridding.")
    parser.add_argument("--target", type=str, default="DANRA", choices=["DANRA", "ERA5"], help="Known targets for regridding. Provide instead of --target-dataset.")

    args = parser.parse_args()

    assert any([args.target_dataset, args.target]), "Either --target-dataset or --target must be provided."

    weights_file = args.weights_file
    output_path = args.output_path

    data = xr.open_zarr(args.input_path)
    if args.target == "DANRA":
        ds_w_target_grid = xr.open_zarr("s3://danra/v0.5.0/single_levels.zarr", storage_options={"profile":"ewc_danra"})
    elif args.target == "ERA5":
        args.target_dataset = "s3://era5/v0.5.0/single_levels.zarr/"
    else:
        ds_w_target_grid = xr.open_zarr(args.target_dataset, storage_options={"profile":"ewc_danra"})

    ds_out = regrid(data, ds_w_target_grid, weights_file)
    ds_out.to_zarr(output_path, mode="w", consolidated=True)