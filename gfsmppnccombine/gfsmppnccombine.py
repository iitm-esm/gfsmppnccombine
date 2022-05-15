#!/usr/bin/env python3

import xarray as xr
import xesmf as xe
import numpy as np
import copy
import glob


REGRIDDERS={}

def _get_vars_contain_lon(ds):
    vars = []
    for var in ds.variables:
        if var in ds[var].coords: continue
        if 'lon' in ds[var].coords:
            vars.append(var)
    return vars

def _get_vars_contain_lat(ds):
    vars = []
    for var in ds.variables:
        if var in ds[var].coords: continue
        if 'lat' in ds[var].coords:
            vars.append(var)
    return vars

def _get_lonsperlat(ds):
    return ds['lon'].attrs['lonsperlat']

def _get_decomp(ds):
    decomp = ds['lat'].attrs['decomp_gfs']
    return decomp

def get_globalNlat(ds):
    return ds['lat'].attrs['domain_decomposition'][1]

def set_regridders(ds, method='nearest_s2d'):
    global REGRIDDERS
    lon = ds['lon']
    maxlon = lon.shape[0]
    ds_out = xr.Dataset({ 
        "lat": (["lat"], [0.0]),
        "lon": (["lon"], lon.values),
        })
    lonsperlat = _get_lonsperlat(ds)
    for nlon in lonsperlat:
        if nlon == maxlon: continue
        indx = (maxlon, nlon, method,)
        if indx in REGRIDDERS: continue 
        dlon = 360.0/nlon
        olon = [0.0,]
        for i in range(1,nlon):
            olon.append(olon[i-1]+dlon)
        ds_in = xr.Dataset({ 
            "lat": (["lat"], [0.0]),
            "lon": (["lon"], olon),
            })
        REGRIDDERS[indx] = xe.Regridder(
            ds_in=ds_in, 
            ds_out=ds_out, 
            method=method, 
            periodic=True,
            reuse_weights=True
            )
    return maxlon, method

def regrid_red2reg(ds, method='nearest_s2d'):
    vars = _get_vars_contain_lon(ds)
    lonsperlat = _get_lonsperlat(ds)
    maxlon, _ = set_regridders(ds,method)
    for var in vars:
        if len(ds[var].shape) == 2:
            # lat, lon
            for lat in range(ds[var].shape[0]):
                nlon = lonsperlat[lat]
                if nlon==maxlon: continue
                #print(f'nlon={nlon}')
                regridder = REGRIDDERS[(maxlon, nlon, method,)]
                data_in = ds[var].values[lat:lat+1,0:nlon]
                ds[var].values[lat:lat+1,:] = regridder(data_in)
        elif len(ds[var].shape) == 3:
            # [time or lev], lat, lon
            for t in range(ds[var].shape[0]):
                for lat in range(ds[var].shape[1]):
                    nlon = lonsperlat[lat]
                    if nlon==maxlon: continue
                    #print(f'nlon={nlon}')
                    regridder = REGRIDDERS[(maxlon, nlon, method,)]
                    data_in = ds[var].values[t,lat:lat+1,0:nlon]
                    ds[var].values[t,lat:lat+1,:] = regridder(data_in)
        elif len(ds[var].shape) == 4:
            # time, lev, lat, lon
            for t in range(ds[var].shape[0]):
                for k in range(ds[var].shape[1]):
                    for lat in range(ds[var].shape[2]):
                        nlon = lonsperlat[lat]
                        if nlon==maxlon: continue
                        #print(f'nlon={nlon}')
                        regridder = REGRIDDERS[(maxlon, nlon, method,)]
                        data_in = ds[var].values[t,k,lat:lat+1,0:nlon]
                        ds[var].values[t,k,lat:lat+1,:] = regridder(data_in)
    ds['lon'].attrs.pop('lonsperlat')

def create_combine_ds(ds):
    ds_out = ds.drop_dims('lat')
    nlatGlobal = get_globalNlat(ds)
    for var in _get_vars_contain_lat(ds):
        shp = list(ds[var].shape)
        latDimIdx = len(shp) - 2
        shp[latDimIdx] = nlatGlobal
        ds_out[var] = xr.DataArray(
            data=np.zeros(shp,dtype=ds[var].dtype),
            dims=ds[var].dims,
            attrs=ds[var].attrs
        )
    lat_attrs = copy.deepcopy(ds['lat'].attrs)
    lat_attrs.pop('decomp_gfs')
    lat_attrs.pop('domain_decomposition')
    lat_data = np.array(range(nlatGlobal),dtype=ds['lat'].dtype)
    ds_out['lat'] = xr.DataArray(data=lat_data, dims=["lat"], attrs=lat_attrs)
    lon = copy.deepcopy(ds['lon'])
    lon.attrs.pop('domain_decomposition')
    lon.attrs.pop('lonsperlat')
    ds_out['lon'] = lon
    
    return ds_out

def update_combine_ds(ds_out,ds):
    i = 0
    decomp=_get_decomp(ds)
    for i in range(len(decomp)):
        j = decomp[i]-1
        ds_out['lat'].values[j] = ds['lat'].values[i]
        for var in _get_vars_contain_lat(ds):
            if len(ds_out[var].shape) == 2:
                ds_out[var].values[j,:] = ds[var].values[i,:]
            elif len(ds_out[var].shape) == 3:
                ds_out[var].values[:,j,:] = ds[var].values[:,i,:]
            elif len(ds_out[var].shape) == 4:
                ds_out[var].values[:,:,j,:] = ds[var].values[:,:,i,:]
            else:
                raise Exception('Wrong variable dimension')


if __name__ == "__main__":
    in_file="testData/gfs_2015_02_05_09.nc"
    in_files = glob.glob(in_file+'.????')
    ds_out = None
    for ifile in in_files:
        ds = xr.open_dataset(ifile,decode_cf=False)
        if ds_out is None:
            ds_out = create_combine_ds(ds)
        regrid_red2reg(ds)
        update_combine_ds(ds_out,ds)
    ds_out.to_netcdf(path=in_file,mode='w')