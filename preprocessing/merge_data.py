import subprocess
from pathlib import Path

# variable_list = ["tas", "tasmax", "tasmin", "pr", "ps", "sfcwind", "rsds", "rlds", "hurs", "huss"]
variable_list = ["tas", "pr"]
# out of "GSWP3", "GSWP3+ERA5" etc. see source_base for more datasets.
dataset = "GSWP3-W5E5"

source_base = Path(
    "/p/projects/isimip/isimip/data/obsclim_harmonization/data_out_pp_combined_backup_for_attrici_paper/"
)

source_dir = source_base #/ dataset

output_base = Path("/p/tmp/sitreu/attrici/input/")

output_dir = output_base / dataset
output_dir.mkdir(parents=True, exist_ok=True)


for variable in variable_list:

    output_file = output_dir / Path(variable + "_" + dataset.lower() + "_merged.nc4")

    cmd = (
        "module load cdo && cdo mergetime "
        + str(source_dir)
        + "/"
        + dataset.lower()
        + "_obsclim_"
        + variable
        + "_global_daily"
        + "_????_????.nc* "
        + str(output_file)
    )
    print(cmd)
    subprocess.check_call(cmd, shell=True)
