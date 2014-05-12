""" pandashp: read/write shapefiles to/from special DataFrames

Offers two functions read_shp and write_shp that convert ESRI shapefiles to
pandas DataFrames that can be manipulated at will and then written back to
shapefiles. Opens up data manipulation capabilities beyond a simple GIS field
calculator.

Usage:
    import pandashp as pdshp
    # calculate population density from shapefile of cities (stupid, I know)
    cities = pdshp.read_shp('cities_germany_projected')
    cities['popdens'] = cities['population'] / cities['area']
    pdshp.write_shp(cities, 'cities_germany_projected_popdens')

"""
__all__ = ["read_shp", "write_shp", "match_vertices_and_edges"]

import itertools
import numpy as np
import pandas as pd
import shapefile
import shapelytools
import warnings
from shapely.geometry import LineString, Point, Polygon

def read_shp(filename):
    """Read shapefile to dataframe w/ geometry.
    
    Args:
        filename: ESRI shapefile name to be read  (without .shp extension)
        
    Returns:
        pandas DataFrame with column geometry, containing individual shapely
        Geometry objects (i.e. Point, LineString, Polygon) depending on 
        the shapefiles original shape type
    
    """
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
        geometries = [Point(*shape.points[0]) for shape in sr.iterShapes()]
    else:
        raise NotImplementedError
    
    data = [r+[g] for r,g in itertools.izip(records, geometries)]
    
    df = pd.DataFrame(data, columns=cols)
    df = df.convert_objects(convert_numeric=True)
    return df

def write_shp(filename, dataframe):
    """Write dataframe w/ geometry to shapefile.
    
    Args:
        filename: ESRI shapefile name to be written (without .shp extension)
        dataframe: a pandas DataFrame with column geometry and homogenous 
                   shape types (Point, LineString, or Polygon)
        
    Returns:
        Nothing.

    """
    
    df = dataframe.copy()
    df.reset_index(inplace=True)
    
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
        column = str(column) # unicode strings freak out pyshp, so remove u'..'
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
    
    
def match_vertices_and_edges(vertices, edges):
    """Adds unique IDs to vertices and corresponding edges.
    
    Identifies, which nodes coincide with the endpoints of edges and creates
    matching IDs for matching points, thus creating a node-edge graph whose
    edges are encoded purely by node ID pairs.
    
    Adds/modifies columns 'Vertex1' and 'Vertex2' in DataFrame edges to reflect 
    the IDs of the nodes DataFrame which the edges touch. IDs are taken from 
    the nodes index.
    
    Args:
        vertices: pandas DataFrame with geometry column of type Point
        edges pandas DataFrame with geometry column of type LineString
        
    Returns:
        Nothing, the arguments are modified in place. The modified vertices
        and edges can be directly used in dhmin, capmin.
    """
    
    vertex_indices = []
    for e, line in enumerate(edges.geometry):
        edge_endpoints = []
        for k, vertex in enumerate(vertices.geometry):
            if line.touches(vertex) or line.intersects(vertex):
                edge_endpoints.append(vertices.index[k])
        
        if len(edge_endpoints) == 0:
            warnings.warn("edge " + str(e) + " has no endpoints: " + str(edge_endpoints))
        elif len(edge_endpoints) == 1:
            warnings.warn("edge " + str(e) + " has only 1 endpoint: " + str(edge_endpoints))
        
        vertex_indices.append(edge_endpoints)
    
    edges['Vertex1'] = pd.Series([min(n1n2) for n1n2 in vertex_indices],
                                index=edges.index)
    edges['Vertex2'] = pd.Series([max(n1n2) for n1n2 in vertex_indices],
                                index=edges.index)

def find_closest_edge(polygons, edges, to_attr='index', column='nearest'):
    """Find closest edge for centroid of polygons.
    
    Args:
        polygons: a pandashp DataFrame of Polygons
        edges: a pandashp DataFrame of LineStrings
        to_attr: a column name in DataFrame edges (default: index)
        column: a column name to be added/overwrite in DataFrame polygons with
                the value of colun to_attr in the nearest row of DataFrame edges
    
    Returns:
        a list of LineStrings connecting polygons' centroids with the nearest 
        point in in edges. Side effect: polygons recieves new column with the 
        attribute value of nearest edge. Warning: if column exists, it is 
        overwritten.
    
    """
   
    connecting_lines = []
    nearest_indices = []
    centroids = [b.centroid for b in polygons['geometry']]
    
    for centroid in centroids:
        nearest_edge, _, nearest_index = shapelytools.closest_object(
                                         edges['geometry'], centroid)
        nearest_point = shapelytools.project_point_to_object(centroid, nearest_edge)
        
        connecting_lines.append(LineString(tuple(centroid.coords) + 
                                           tuple(nearest_point.coords)))
        
        nearest_indices.append(edges[to_attr][nearest_index])
    
    polygons[column] = pd.Series(nearest_indices, index=polygons.index)
    
    return connecting_lines