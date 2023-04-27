import os
import glob
import subprocess
from pathlib import Path
import xarray as xr
import settings as s


remove_intermediate_files = True

variable_list = ["tas"]
#variable_list = ["hurs", "tas", "pr6", "rg", "tasrange", "tasskew", "ws"]
#variable_list = ["tas", "tasmax", "tasmin", "pr6", "rg", "ps", "sfcwind", "rsds", "rlds", "hurs", "huss"]
timespane_list = ["1950_1989", "1990_2020"] # 
time_hour = "12"
tile_list = ["00023"]

source_base = Path(
    #"/p/tmp/dominikp/meteo_data/BASD_c_attrici_test/"
    "/p/projects/ou/rd3/dmcci/basd_era5-land_to_efas-meteo/basd_output_data/"
)

source_dir = source_base 

output_base = Path("/p/tmp/annabu/attrici_interpolation/meteo_data/")

output_dir = output_base / s.dataset 
output_dir.mkdir(parents=True, exist_ok=True)


for variable in variable_list:
    
    for tile in tile_list:
    
        for timespane in timespane_list:
        
            meteo_file = str(source_dir) + "/" + f"{s.dataset}_{variable}{time_hour}_{s.dataset}_{timespane}_t_{tile}_ba.nc"
            output_file_ncpdq = output_dir / Path(variable + time_hour + "_" + s.dataset.lower() + "_" + timespane + "_" + tile + "_ba_n_tmp.nc4")
            timeunit_year = timespane.split('_')[0]

            ## set all facts to same dimension order
            cmd = (
                "module load nco && ncpdq -4 -a time,lon,lat " + meteo_file + " " + str(output_file_ncpdq)
            )
            print(cmd)
            subprocess.check_call(cmd, shell=True)

            ## repair time unit from hour to daily
            output_file_setreftime = output_dir / Path(variable + time_hour + "_" + s.dataset.lower() + "_" + timespane + "_" + tile + "_ba_n_srt_tmp.nc4")
            cmd = (
                f"module load cdo && cdo -setreftime,{timeunit_year}-01-01,{time_hour}:00:00,1day "
                + str(output_file_ncpdq)
                + " " 
                + str(output_file_setreftime) 
            )
            print(cmd)
            subprocess.check_call(cmd, shell=True)

            ## Interpolation test subset: crop to spatial subset to nth x nth cells
            meteo = xr.load_dataset(output_file_setreftime)
            meteo_clipped_file = str(output_dir) + "/" + variable + time_hour + "_" + s.dataset.lower() + "_" + timespane + "_" + tile + "_ba_n_srt_c_tmp.nc4"
            print(meteo) 
            meteo_clipped = meteo.isel(lon=slice(0,s.file_len), lat=slice(0, s.file_len))  # select by index
            print(meteo_clipped)
            meteo_clipped.to_netcdf(meteo_clipped_file)
            meteo_clipped.close()
            print("clipping by spatial index - done")


        # merge separated nc files by variable to one merged nc file
        output_file_mergetime = output_dir / Path(variable + time_hour + "_" + s.dataset.lower() + "_" + "1950_2020" + "_" + tile +"_ba_n_srt_c_merged_tmp.nc4")
        print(f"\nwriting to {output_file_mergetime}:") 
        cmd = (
            "module load cdo && cdo mergetime " 
            + str(output_dir) + "/" + variable + time_hour + "_" + s.dataset.lower() 
            + "_????_????_"
            + tile + "_ba_n_srt_c.nc4"
            + " "
            + str(output_file_mergetime)
        )
        print(cmd)
        subprocess.check_call(cmd, shell=True)

        ## reorder dimensions of fact file
        meteo = xr.load_dataset(output_file_mergetime)
        meteo_dim_file = str(output_dir) + "/" + variable + time_hour + "_" + s.dataset.lower() + "_" + "1950_2020" + "_" + tile + "_ba_merged.nc4"
        print(meteo) 
        meteo_dim = meteo
        meteo_dim["tas"] = meteo_dim["tas"].transpose("time", "lat", "lon")
        print(meteo_dim)
        meteo_dim.to_netcdf(meteo_dim_file, format="NETCDF4")
        meteo_dim.close()
        print("clipping by spatial index - done")


if remove_intermediate_files == True:
    for tmp_files in glob.iglob(os.path.join(dir, '*_tmp.*')):
        os.remove(tmp_files)
    print(f"Removing temporary files")
