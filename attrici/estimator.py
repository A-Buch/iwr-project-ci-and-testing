import os
import numpy as np
import pandas as pd
import pymc3 as pm
from datetime import datetime
import netCDF4 as nc
from pathlib import Path
#import psutil
from time import sleep
import xarray as xr

import attrici.datahandler as dh
import attrici.const as c
import attrici.models as models
import attrici.fourier as fourier
import attrici.postprocess as pp
import settings as s
import pickle


model_for_var = {
    "tas": models.Tas,
    "tasrange": models.Tasrange,
    "tasskew": models.Tasskew,
    "pr": models.Pr,
    "hurs": models.Hurs,
    "wind": models.Wind,
    "sfcwind": models.Wind,
    "ps": models.Ps,
    "rsds": models.Rsds,
    "rlds": models.Rlds,
}


class estimator(object):
    def __init__(self, cfg):

        self.output_dir = cfg.output_dir
        self.draws = cfg.draws
        self.cores = cfg.ncores_per_job
        self.chains = cfg.chains
        self.tune = cfg.tune
        self.subset = cfg.subset
        self.seed = cfg.seed
        self.progressbar = cfg.progressbar
        self.variable = cfg.variable
        self.modes = cfg.modes
        self.f_rescale = c.mask_and_scale[cfg.variable][1]
        self.save_trace = cfg.save_trace
        self.report_variables = cfg.report_variables
        self.inference = cfg.inference
        self.startdate = cfg.startdate

        try:
            #TODO remove modes from initialization
            self.statmodel = model_for_var[self.variable](self.modes)

        except KeyError as error:
            print(
                "No statistical model for this variable. Probably treated as part of other variables."
            )
            raise error


    def estimate_parameters(self, time, out, df, lat, lon, lat_idx, lon_idx, map_estimate):
        x_fourier = fourier.get_fourier_valid(df, self.modes)
        x_fourier_01 = (x_fourier + 1) / 2
        x_fourier_01.columns = ["pos" + col for col in x_fourier_01.columns]

        dff = pd.concat([df, x_fourier, x_fourier_01], axis=1)
        df_subset = dh.get_subset(dff, self.subset, self.seed, self.startdate)

        self.model = self.statmodel.setup(df_subset)

        outdir_for_cell = dh.make_cell_output_dir(
            self.output_dir, "traces", lat, lon, self.variable
        )
        if map_estimate:
            try:
                print("Redo parameter estimation and writing parameters to file.")
                with open(outdir_for_cell, 'rb') as handle:
                    free_params = pickle.load(handle) ## load from trace.h5 files

                # write the values of each parameter as single layers to nc file, i.e. one parameter can contain 1 to n layers
                param_names = list(free_params.keys())
                for param_name in param_names:
                    values_per_parameter = np.atleast_1d(np.array(free_params[param_name])) # forcing 0-D arrays to 1-D
                    ## ## create empty variable in netcdf if not exists
                    if param_name in out.variables.keys():
                        pass
                    else:
                        out.createVariable(param_name, "f4", ("time", "lat", "lon"), chunksizes=(time.shape[0], 1, 1), fill_value=1e20) 
                    out.variables[param_name][ :, int(lat_idx), int(lon_idx)] = values_per_parameter
                    #for n in range(len(values_per_parameter)):
                        #out.variables[param_name][ n, int(lat_idx), int(lon_idx)] = values_per_parameter[n] #np.array(values_per_parameter[n])
                print(f"wrote all {len(param_names)} to cell position",  int(lat_idx), int(lon_idx))

            ## TODO: check if unnecessary
            except Exception as e:
                print("Problem with saved trace:", e, ". Redo parameter estimation.")
                trace = pm.find_MAP(model=self.model)
                free_params = {key: value for key, value in trace.items()
                                       if key.startswith('weights') or key=='logp'}
                if self.save_trace:
                    with open(outdir_for_cell, 'wb') as handle:
                        pickle.dump(free_params, handle, protocol=pickle.HIGHEST_PROTOCOL)

                # write the values of each parameter as single layers to nc file, i.e. one parameter can contain 1 to n layers
                param_names = list(free_params.keys())
                for param_name in param_names:
                    values_per_parameter = np.atleast_1d(np.array(free_params[param_name])) # forcing 0-D arrays to 1-D
                    ## ## create empty variable in netcdf if not exists
                    if param_name in out.variables.keys():
                        pass
                    else:
                        out.createVariable(param_name, "f4", ("time", "lat", "lon"), chunksizes=(time.shape[0], 1, 1), fill_value=1e20) 
                    out.variables[param_name][ :, int(lat_idx), int(lon_idx)] = values_per_parameter
                print(f"wrote all {len(param_names)} to cell position",  int(lat_idx), int(lon_idx))

        else:
            # FIXME: Rework loading old traces
            # print("Search for trace in\n", outdir_for_cell)
            # As load_trace does not throw an error when no saved data exists, we here
            # test this manually. FIXME: Could be improved, as we check for existence
            # of names and number of chains only, but not that the data is not corrupted.
            try:
                free_params = pm.load_trace(outdir_for_cell, model=self.model)
                print(free_params.varnames)
                #     for var in self.statmodel.vars_to_estimate:
                #         if var not in free_params.varnames:
                #             print(var, "is not in free_params, rerun sampling.")
                #             raise IndexError
                #     if free_params.nchains != self.chains:
                #         raise IndexError("Sample data not completely saved. Rerun.")
                print("Successfully loaded sampled data from")
                print(outdir_for_cell)
                print("Skip this for sampling.")

                # write the values of each parameter as single layers to nc file, i.e. one parameter can contain 1 to n layers
                param_names = list(free_params.keys())
                for param_name in param_names:
                    values_per_parameter = np.atleast_1d(np.array(free_params[param_name])) # amount of values for certain parameter by forcing 0-D arrays to 1-D
                    ## ## create empty variable in netcdf if not exists
                    if param_name in out.variables.keys():
                        pass
                    else:
                        out.createVariable(param_name, "f4", ("time", "lat", "lon"), chunksizes=(time.shape[0], 1, 1), fill_value=1e20) 
                    print("writing", len(values_per_parameter), "value(s) of parameter", param_name)
                    out.variables[param_name][ :, int(lat_idx), int(lon_idx)] = values_per_parameter
                print(f"wrote all {len(param_names)} to cell position",  int(lat_idx), int(lon_idx))

            except Exception as e:
                print("Problem with saved trace:", e, ". Redo parameter estimation.")
                trace = self.sample()
                # print(pm.summary(trace))  # takes too much memory
                if self.save_trace:
                    pm.backends.save_trace(trace, outdir_for_cell, overwrite=True)

                free_params = {key: value for key, value in trace.items()
                               if key.startswith('weights') or key=='logp'}
                # write the values of each parameter as single layers to nc file, i.e. one parameter can contain 1 to n layers
                param_names = list(free_params.keys())
                for param_name in param_names:
                    values_per_parameter = np.atleast_1d(np.array(free_params[param_name])) # amount of values for certain parameter by forcing 0-D arrays to 1-D
                    ## ## create empty variable in netcdf if not exists
                    if param_name in out.variables.keys():
                        pass
                    else:
                        out.createVariable(param_name, "f4", ("time", "lat", "lon"), chunksizes=(time.shape[0], 1, 1), fill_value=1e20) 
                    print("writing", len(values_per_parameter), "value(s) of parameter", param_name)
                    out.variables[param_name][ :, int(lat_idx), int(lon_idx)] = values_per_parameter
                print(f"wrote all {len(param_names)} to cell position",  int(lat_idx), int(lon_idx))

        return dff, free_params



    def load_parameters(self, parameter_f, df, lat_idx, lon_idx, map_estimate):
        x_fourier = fourier.get_fourier_valid(df, self.modes)
        x_fourier_01 = (x_fourier + 1) / 2
        x_fourier_01.columns = ["pos" + col for col in x_fourier_01.columns]

        dff = pd.concat([df, x_fourier, x_fourier_01], axis=1)
        df_subset = dh.get_subset(dff, self.subset, self.seed, self.startdate)

        self.model = self.statmodel.setup(df_subset)

        ## load free_parameters from nc file
        free_parameters = {}
        parameter_names = list(parameter_f.keys())

        print("lat_idx, lon_idx", lat_idx, lon_idx)
        for parameter_name in parameter_names:
            param_values = parameter_f[parameter_name][:, int(lat_idx), int(lon_idx)]
            ## TODO: make this nicer: clip parameters to their amount of values per cell, usually 1 layer or <8 layers
            param_values = param_values[ ~np.isnan(param_values)]  ## TODO improve by defining flexible z-dimension of paramters.nc
            free_parameters[parameter_name] = param_values.data.astype('float').squeeze()  # float64, remove entries with nan
        return dff, free_parameters


    def sample(self):

        TIME0 = datetime.now()

        if self.inference == "NUTS":
            with self.model:
                trace = pm.sample(
                    draws=self.draws,
                    cores=self.cores,
                    chains=self.chains,
                    tune=self.tune,
                    progressbar=self.progressbar,
                    target_accept=.95
                )
            # could set target_accept=.95 to get smaller step size if warnings appear
        elif self.inference == "ADVI":
            with self.model:
                mean_field = pm.fit(
                    n=10000, method="fullrank_advi", progressbar=self.progressbar
                )
                # TODO: trace is just a workaround here so the rest of the code understands
                # ADVI. We could communicate parameters from mean_fied directly.
                trace = mean_field.sample(1000)
        else:
            raise NotImplementedError

        TIME1 = datetime.now()
        print(
            "Finished job {0} in {1:.0f} seconds.".format(
                os.getpid(), (TIME1 - TIME0).total_seconds()
            )
        )

        return trace


    def estimate_timeseries(self, df, trace, datamin, scale, map_estimate, subtrace=1000):
        #print(trace["mu"].shape, df.shape)
        trace_obs, trace_cfact = self.statmodel.resample_missing(
            trace, df, subtrace, self.model, self.progressbar, map_estimate
        )

        df_params = dh.create_ref_df(  ## only mu etc, not weights
            df, trace_obs, trace_cfact, self.statmodel.params
        )
        cfact_scaled = self.statmodel.quantile_mapping(df_params, df["y_scaled"])
        print("Done with quantile mapping.")

        # fill cfact_scaled as is from quantile mapping
        # for easy checking later
        df.loc[:, "cfact_scaled"] = cfact_scaled

        # rescale all scaled values back to original, invalids included
        df.loc[:, "cfact"] = self.f_rescale(df.loc[:, "cfact_scaled"], datamin, scale)

        # populate invalid values originating from y_scaled with with original values
        if self.variable == 'pr':
            df.loc[df['cfact_scaled'] == 0, 'cfact'] = 0
        else:
            invalid_index = df.index[df["y_scaled"].isna()]
            df.loc[invalid_index, "cfact"] = df.loc[invalid_index, "y"]

        # df = df.replace([np.inf, -np.inf], np.nan)
        # if df["y"].isna().sum() > 0:
        yna = df["cfact"].isna()
        yinf = df["cfact"] == np.inf
        yminf = df["cfact"] == -np.inf
        print(f"There are {yna.sum()} NaN values from quantile mapping. Replace.")
        print(f"There are {yinf.sum()} Inf values from quantile mapping. Replace.")
        print(f"There are {yminf.sum()} -Inf values from quantile mapping. Replace.")

        df.loc[yna | yinf | yminf, "cfact"] = df.loc[yna | yinf | yminf, "y"]

        # todo: unifiy indexes so .values can be dropped
        for v in df_params.columns:
            df.loc[:, v] = df_params.loc[:, v].values

        if map_estimate:
            df.loc[:, "logp"] = trace_obs['logp'].mean(axis=0)

        if self.report_variables != "all":
            df = df.loc[:, self.report_variables]

        return df
