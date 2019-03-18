import getpass

user = getpass.getuser()

# this will hopefully avoid hand editing paths everytime.
# fill further for convenience.
if user == "mengel":
	data_dir = "/home/mengel/data/20190306_IsimipDetrend/"
else:
	data_dir = "/home/bschmidt/temp/gswp3/"

#  handle job specifications
n_jobs = 16  # number of childprocesses created by the job

gmt_file = 'test_ssa_gmt.nc4'
to_detrend_file = 'test_data_tas.nc4'