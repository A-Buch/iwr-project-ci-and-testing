"""
The script reorders the dimensions, converts the hourly timestamp to daily (needed for subsequent steps), 
creates a subset for the interpolation test and joins the single timesteps (here 1950-1990, 1990-2020) into one file
"""
import os
import glob
import subprocess
from pathlib import Path
import xarray as xr
import settings as s



remove_intermediate_files = False

variable_list = ["tas"]
#variable_list = ["hurs", "tas", "pr6", "rg", "tasrange", "tasskew", "ws"]
#variable_list = ["tas", "tasmax", "tasmin", "pr6", "rg", "ps", "sfcwind", "rsds", "rlds", "hurs", "huss"]
timespane_list = ["1950_1989", "1990_2020"] # 
time_hour = "12"
tile_list = ["00024"]

source_base = Path(
    #"/p/tmp/dominikp/meteo_data/BASD_c_attrici_test/"
    #"/p/projects/ou/rd3/dmcci/basd_era5-land_to_efas-meteo/basd_output_data/"
    "/mnt/c/Users/Anna/Documents/UNI/HiWi/IWRcourses_PY_ML_meetings/effective_software_testing/iwr-project-ci-and-testing/meteo_data/ERA5"

)


source_dir = source_base 
output_base = Path("/mnt/c/Users/Anna/Documents/UNI/HiWi/IWRcourses_PY_ML_meetings/effective_software_testing/iwr-project-ci-and-testing/meteo_data")

output_dir = output_base / s.dataset 
output_dir.mkdir(parents=True, exist_ok=True)


for variable in variable_list:
    
    for tile in tile_list:
    
        for timespane in timespane_list:
        
            meteo_file = str(source_dir) + "/" + f"{s.dataset}_{variable}{time_hour}_{s.dataset}_{timespane}_t_{tile}_ba.nc"
            output_file_ncpdq = output_dir / Path(variable + time_hour + "_" + s.dataset.lower() + "_" + timespane + "_" + tile + "_ba_n_tmp.nc4")
            timeunit_year = timespane.split('_')[0]

            if not os.path.exists(output_file_ncpdq):
                ## set all factual datasets to same dimension order
                try:
                    cmd = (
                        "module load nco && ncpdq -4 -a time,lat,lon " + meteo_file + " " + str(output_file_ncpdq)
                    )
                    print(cmd)
                    subprocess.check_call(cmd, shell=True)
                except: 
                    cmd = (
                        "ncpdq -4 -a time,lat,lon " + meteo_file + " " + str(output_file_ncpdq)
                    )
                    print(cmd)
                    subprocess.check_call(cmd, shell=True)

            ## set time unit from hour to daily
            output_file_setreftime = output_dir / Path(variable + time_hour + "_" + s.dataset.lower() + "_" + timespane + "_" + tile + "_ba_n_srt_tmp.nc4")
            if not os.path.exists(output_file_setreftime):
                try:
                    cmd = (
                        f"module load cdo && cdo -setreftime,{timeunit_year}-01-01,{time_hour}:00:00,1day "
                        + str(output_file_ncpdq)
                        + " " 
                     + str(output_file_setreftime) 
                    )
                    print(cmd)
                    subprocess.check_call(cmd, shell=True)
                except: 
                    cmd = (
                        f"cdo -setreftime,{timeunit_year}-01-01,{time_hour}:00:00,1day "
                        + str(output_file_ncpdq)
                        + " " 
                        + str(output_file_setreftime) 
                    )
                    print(cmd)
                    subprocess.check_call(cmd, shell=True)


                

            ## Create subset for testing interpolation method
            meteo = xr.load_dataset(output_file_setreftime)
            meteo_clipped_filepath = str(output_dir) + "/" + variable + time_hour + "_" + s.dataset.lower() + "_" + timespane + "_" + tile + "_ba_n_srt_c_tmp.nc4"
            print(meteo) 
            if not os.path.exists(meteo_clipped_filepath):
                meteo_clipped = meteo.isel(lon=slice(0,s.file_len), lat=slice(0, s.file_len))  # select by index
                print(meteo_clipped)
                meteo_clipped.to_netcdf(meteo_clipped_filepath)
                meteo_clipped.close()
                print("clipping by spatial index - done")


        # merge multiple nc files by variable to into one large nc file
        output_file_mergetime = output_dir / Path(variable + time_hour + "_" + s.dataset.lower() + "_" + "1950_2020" + "_" + tile +"_ba_n_srt_c_merged_tmp.nc4")
        print(f"\nwriting to {output_file_mergetime}:") 
        
        if not os.path.exists(output_file_mergetime):
            try:
                cmd = (
                    "module load cdo && cdo mergetime " 
                    + str(output_dir) + "/" + variable + time_hour + "_" + s.dataset.lower() 
                    + "_????_????_"
                    + tile + "_ba_n_srt_c_tmp.nc4"
                   + " "
                    + str(output_file_mergetime)
                )
                print(cmd)
                subprocess.check_call(cmd, shell=True)
            except:
                cmd = (
                    "cdo mergetime " 
                    + str(output_dir) + "/" + variable + time_hour + "_" + s.dataset.lower() 
                    + "_????_????_"
                    + tile + "_ba_n_srt_c_tmp.nc4"
                   + " "
                    + str(output_file_mergetime)
                )
                print(cmd)
                subprocess.check_call(cmd, shell=True)


if remove_intermediate_files == True:
    for tmp_files in glob.iglob(os.path.join(output_dir, '*_tmp.nc*')):
        os.remove(tmp_files)
    print(f"Removing temporary files")
