# Python-Tools

This is a collection of small modules that I often/sometimes/not anymore use for my day-to-day scripting needs. I keep them in a separate directory that I [keep always on the Python search path](http://stackoverflow.com/q/17806673/2375855) so that I can include them like installed site-packages.


## pandashp

Basically my private implementation of a [GeoPandas](http://geopandas.org/) `GeoFrame`. This module provides two functions, `read_shp` and `write_shp`. The first one reads an ESRI shapefile to a pandas DataFrame, saving the geometry information (Points, Lines, Polygons) in the column `geometry`. The second function does the reverse. These functions do not care about transformations, much different to GeoPandas. I plan to migrate to using Geopandas myself, so better don't use this.

### Dependencies
  - [pandas](http://pandas.pydata.org/)
  - [pyshp](https://github.com/GeospatialPython/pyshp)
  - [shapely](https://pypi.python.org/pypi/Shapely) (and `shapelytools` below)
  
  
## pandaspyomo

Provides functions like `get_entity` to read data from coopr.pyomo models to pandas DataFrames. Unfortunately, pyomo changed its internals some time around the 3.5 release version, so these functions don't work with current pyomo versions. See [URBS](https://github.com/tum-ens/urbs) for an up-to-date version of these functions.

### Dependencies
  - [Coopr](https://software.sandia.gov/trac/coopr/wiki/WikiStart)
  - [pandas](http://pandas.pydata.org/)
  
  
## pyomotools

Archive for some misc functions needed for migrating [URBS](https://github.com/tum-ens/urbs) from GAMS to Python. Function `read_xls` for example implements automatic detection of Capital lettre column titles for onset detection. I don't use it any longer.

### Dependencies
  - [pandas](http://pandas.pydata.org/)
  
  
## shapelytools

Many handy small functions dealing with collections of shapely objects, i.e. points, lines and polygons. I use them to script small geographic algorithms on my own. The module implements a naive nearest neighbor algorithm, pruning of short line segments, finding isolated endpoints among a list of possibly touching lines. **Note:** shapely is not aware of geographic coordinates! So while some of these functions might work with lat/lon coordinates in degrees, I use them mainly in projected coordinate systems with x/y coordinates in metres.

### Dependencies
  - [shapely](https://pypi.python.org/pypi/Shapely)


## shptools

Convenience wrapper of pyshp, including automatic type detection (numeric, string) when reading/writing shapefiles. Might be not needed anymore, but was quite handy when written. I mainly use `pandashp` above nowadays because of the much more mighty DataFrame.

### Dependencies
  - [pyshp](https://github.com/GeospatialPython/pyshp)
  - [shapely](https://pypi.python.org/pypi/Shapely) (and `shapelytools` below)
  

## skeletrontools

Wrapper module that provides function `skeletonize`, which reads in a pandashp DataFrame of road segments and returns a simplified version of it. The most expensive step is the skeletonization of a buffered version of this road network, decorated with some pre- and postprocessing steps.

### Dependencies
  - `pandashp` above
  - [Skeletron](https://pypi.python.org/pypi/Skeletron/0.9.2) and its dependencies