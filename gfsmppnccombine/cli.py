'''
Copyright 2019 ARC Centre of Excellence for Climate Extremes

author: Aidan Heerdegen <aidan.heerdegen@anu.edu.au>

Licensed under the Apache License, Version 2.0 (the 'License');
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an 'AS IS' BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''
import os
import sys
import argparse
import xarray as xr
import glob
from gfsmppnccombine import create_combine_ds, regrid_red2reg, update_combine_ds, get_time_var 

def parse_args(args):

    parser = argparse.ArgumentParser(description='Regrids the gfs_nc_io produced netCDF files from reduced grid to regular grid')

    parser.add_argument('--verbose', 
                        help='Verbose output', 
                        action='store_true')
    parser.add_argument('-o','--outputdir', 
                        help='Output directory in which to store the data', 
                        default='.')
    parser.add_argument('--overwrite', 
                        help='Overwrite output file if it already exists', 
                        action='store_true')
    parser.add_argument('inputs', help='netCDF files', nargs='+')

    return parser.parse_args(args)

def main_parse_args(args):
    '''
    Call main with list of arguments. Callable from tests
    '''
    # Must return so that check command return value is passed back to calling routine
    # otherwise py.test will fail
    return main(parse_args(args))

def main_argv():
    '''
    Call main and pass command line arguments. This is required for setup.py entry_points
    '''
    main_parse_args(sys.argv[1:])

def main(args):
    for file_path in args.inputs:
        in_file=file_path
        in_files = glob.glob(in_file+'.????')
        ds_out = None
        for ifile in in_files:
            ds = xr.open_dataset(ifile,decode_cf=False)
            if ds_out is None:
                ds_out = create_combine_ds(ds)
            regrid_red2reg(ds)
            update_combine_ds(ds_out,ds)
        ds_out.to_netcdf(path=in_file,mode='w',unlimited_dims=get_time_var(ds))


if __name__ == '__main__':
    main_argv()
