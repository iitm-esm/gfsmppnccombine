# gfsmppnccombine 

[//]: # [![Build Status](https://travis-ci.org/coecms/gfsmppnccombine.svg?branch=master)](https://travis-ci.org/coecms/gfsmppnccombine)
[//]: # [![codecov.io](http://codecov.io/github/coecms/gfsmppnccombine/coverage.svg?branch=master)](http://codecov.io/github/coecms/gfsmppnccombine?branch=master)

Combines gfs_nc_io produced distributed netCDF files and regrids from reduced grid to regular grid

## Install

    mamba install xesmf
    git clone https://github.com/iitm-esm/gfsmppnccombine
    cd gfsmppnccombine
    pip install .

## Program Invocation

### Usage

`gfsmppnccombine` is  a command line program. 

    usage: gfsmppnccombine inputs [inputs ...]

    positional arguments:
    inputs                netCDF files generated using gfs_nc_io
