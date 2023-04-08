import os
import glob
import subprocess
from pathlib import Path



variable_list = ["tas"]
#variable_list = ["tx", "tn", "apdt", "tas", "tasrange", "tasskew"]  # tx, tn=tasmax, tasmin
#variable_list = ["hurs", "tas", "pr6", "rg", "tasrange", "tasskew", "ws"]
#variable_list = ["tas", "tasmax", "tasmin", "pr6", "rg", "ps", "sfcwind", "rsds", "rlds", "hurs", "huss"]
dataset = "ERA5"
timespane_list = ["1950_1989", "1990_2020"] # 
time_hour = "12"
tile_list = ["00024"]

source_base = Path(
    #"/p/projects/isimip/isimip/data/obsclim_harmonization/data_out_pp_combined_backup_for_attrici_paper/"
    #"/p/tmp/dominikp/meteo_data/BASD_c_attrici_test/"
    "/p/projects/ou/rd3/dmcci/basd_era5-land_to_efas-meteo/basd_output_data/"
    #"/p/tmp/annabu/attrici_interpolation/meteo_data/ERA5/testarea_3001/"
)

source_dir = source_base 

output_base = Path("/p/tmp/annabu/attrici_interpolation/meteo_data/")

output_dir = output_base / dataset 
output_dir.mkdir(parents=True, exist_ok=True)


for variable in variable_list:
    
    for tile in tile_list:
    
        for timespane in timespane_list:
     
            output_file_ncpdq = output_dir / Path(variable + time_hour + "_" + dataset.lower() + "_" + timespane + "_" + tile + "_ba_ncpdq.nc")
            timeunit_year = timespane.split('_')[0]
     
            print(f"\npermuate dimensions to time-lon-lat and time unit to daily:") 
            # permutate dimensions to obtain a lonlat grid (lon,lat=grid) from a generic grid (where time,lat=grid)
            cmd = (
                "module load nco && ncpdq -4 -a time,lon,lat "  # -4 = as NECDF4
                + str(source_dir)
                + "/"
                + f"{dataset}"
                + "_"
                + variable
                + time_hour   #  12 oclock, 
                + "_"
                + dataset 
                + "_"
                + timespane
                + "_t_"   # last tile of 25 tiles per timespane, 
                + tile
                + "_ba.nc"  # ???? == 4 unknown letter e.g. year
                + " "
                + str(output_file_ncpdq)
            )
            print(cmd)
            subprocess.check_call(cmd, shell=True)
            
            ## fix time unit from hour to daily
            output_file_setreftime = output_dir / Path(variable + time_hour + "_" + dataset.lower() + "_" + timespane + "_" + tile + "_ba_setreftime.nc")
            cmd = (
                f"module load cdo && cdo -setreftime,{timeunit_year}-01-01,{time_hour}:00:00,1day "
                + str(output_file_ncpdq)
                + " " 
                + str(output_file_setreftime) 
            )
            print(cmd)
            subprocess.check_call(cmd, shell=True)
     
        
        # merge separated nc files by variable to one merged nc file
        output_file_mergetime = output_dir / Path(variable + time_hour + "_" + dataset.lower() + "_" + "1950_2020" + "_" + tile +"_ba_ncpdq_merged.nc")
        print(f"\nwriting to {output_file_mergetime}:") 
        cmd = (
            "module load cdo && cdo mergetime " 
            + str(output_dir) + "/" + variable + time_hour + "_" + dataset.lower() + "_????_????_" + tile + "_ba_setreftime.nc4"  # infiles from output_file_setreftime
            + " "
            + str(output_file_mergetime)
        )
        print(cmd)
        subprocess.check_call(cmd, shell=True)



# remove intermediate files
for r in glob.glob([str(output_dir)+"/*_ba_setreftime.nc", str(output_dir)+"/*_ba_ncpdq.nc"], recursive=True):
    try:
        os.remove(r)
    except e:
        print("Couldnt find file: ", r)