""" I/O functionality for manipulating shapefiles with DataFrames """
import itertools
import numpy as np
import pandas as pd
import shapefile
from shapely.geometry import LineString, Point, Polygon

def read_shp(filename):
    """Read shapefile to dataframe w/ geometry."""
    sr = shapefile.Reader(filename)
    
    cols = sr.fields[:] # [:] = duplicate field list
    if cols[0][0] == 'DeletionFlag':
        cols.pop(0)
    cols = [col[0] for col in cols] # extract field name only
    cols.append('geometry')
    
    records = [row for row in sr.iterRecords()]
    
    if sr.shapeType == shapefile.POLYGON:
        geometries = [Polygon(shape.points) for shape in sr.iterShapes()]
    elif sr.shapeType == shapefile.POLYLINE:
        geometries = [LineString(shape.points) for shape in sr.iterShapes()]
    elif sr.shapeType == shapefile.POINT:
        geometries = [Point(shape.points) for shape in sr.iterShapes()]
    else:
        raise NotImplementedError
    
    data = [r+[g] for r,g in itertools.izip(records, geometries)]
    
    df = pd.DataFrame(data, columns=cols)
    df = df.convert_objects(convert_numeric=True)
    return df

def write_shp(dataframe, filename):
    """Write dataframe w/ geometry to shapefile."""
    
    df = dataframe.copy()
    
    # split geometry column from dataframe
    geometry = df.pop('geometry')
        
    # write geometries to shp/shx, according to geometry type
    if isinstance(geometry[0], Point):
        sw = shapefile.Writer(shapefile.POINT)
        for point in geometry:
            sw.point(point.x, point.y)
        
    elif isinstance(geometry[0], LineString):
        sw = shapefile.Writer(shapefile.POLYLINE)
        for line in geometry:
            sw.line([list(line.coords)])
        
    elif isinstance(geometry[0], Polygon):
        sw = shapefile.Writer(shapefile.POLYGON)
        for polygon in geometry:
            sw.poly([list(polygon.exterior.coords)])
    else:
        raise NotImplementedError
        
    # add fields for dbf
    for k, column in enumerate(df.columns):
        if np.issubdtype(df.dtypes[k], np.number):
            if np.issubdtype(df.dtypes[k], np.floating):
                sw.field(column, 'N', decimal=5)
            else:
                sw.field(column, 'N', decimal=0)
        else:
            sw.field(column)
        
    # add records to dbf
    for record in df.itertuples():
        sw.record(*record[1:]) # drop first tuple element (=index)

    sw.save(filename)
    