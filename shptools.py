import itertools
import shapefile
from shapely.geometry import Polygon, MultiLineString, LineString, Point
import pdb

def read_shp(filename):
    """Read contents of a shapefile to a shapely geometry object.

    Usage:
        geometries = read_shp(filename)
        (geometries, records, fields) = read_shp(filename)

    Arguments:
        filename    shapefile name

    Returns:
        geometries  list of shapely geometries (Polygon, LineString, ...)
        records     list of records (list of values), one per geometry
        fields      list of fieldnames of a record
    """
    sr = shapefile.Reader(filename)

    if sr.shapeType == shapefile.POLYGON:
        shapes = sr.shapes()
        geometries = [Polygon(shape.points) for shape in shapes]
        
        fields = sr.fields[:]
        if fields[0][0] == 'DeletionFlag':
            fields.pop(0)
        fields = [field[0] for field in fields] # extract field name only

        records = []
        for record in sr.records():
            for i, value in enumerate(record):
                try:
                    record[i] = float(value) # convert record values to numeric...
                except ValueError:
                    pass # ... if possible

            records.append(record)
        
        return (geometries, records, fields)

    elif sr.shapeType == shapefile.POLYLINE:
        shapes = sr.shapes()
        geometries = [LineString(shape.points) for shape in shapes]

        fields = sr.fields[:] # [:] = duplicate field list
        if fields[0][0] == 'DeletionFlag':
            fields.pop(0)
        fields = [field[0] for field in fields] # extract field name only

        records = []
        for record in sr.records():
            for i, value in enumerate(record):
                try:
                    record[i] = float(value) # convert record values to numeric...
                except ValueError:
                    pass # ... if possible

            records.append(record)

        return (geometries, records, fields)


    elif sr.shapeType == shapefile.MULTIPOINT:
        raise NotImplementedError

    else:
        raise NotImplementedError





def write_shp(filename, geometry, records=[], fields=[]):
    """Write a single shapely MultiLineString or Polygon to a shapefile.

    Argument geometry may also be a list of LineString objects. In that case,
    each entry may have associated data in the optional records list. If
    records is given, fields is the list of fieldnames for the value list in
    each record.

    Usage:
        write_shp(filename, geometry, records=[], fields=[])

    Arguments:
        filename    filename of shapefile
        geometry    a shapely geometry (MultiLineString, Polygon, ...)
        records     optional list of list of values, one per geometry
        fields      optional (implied by records) list of fieldnames
    """

    # SINGLE MULTILINESTRING
    if isinstance(geometry, MultiLineString):
        sw = shapefile.Writer(shapefile.POLYLINE)

        # fields
        sw.field("length")
        sw.field("start-x")
        sw.field("start-y")
        sw.field("end-x")
        sw.field("end-y")
        sw.field("npoints")

        # geometry and record
        for line in geometry:
            sw.line([list(line.coords)])
            sw.record(line.length,
                      line.coords[0][0],
                      line.coords[0][1],
                      line.coords[-1][0],
                      line.coords[-1][1],
                      len(line.coords))
        sw.save(filename)

    # SINGLE POLYGON
    elif isinstance(geometry, Polygon):
        # data
        parts = [list(geometry.exterior.coords)]
        parts.extend(list(interior.coords) for interior in geometry.interiors)

        sw = shapefile.Writer(shapefile.POLYGON)
        sw.field("area")
        sw.poly(parts)
        sw.record(geometry.area)
        sw.save(filename)

    # LISTS
    elif isinstance(geometry, list):

        # check for fields and records
        if (fields and not records) or (not fields and records):
            raise ValueError('Arguments records and fields must both be provided.')

        if records and (len(fields) != len(records[0])):
            raise ValueError('Length of fields and records do not match.')

        # derive field types based on record values
        field_type = {}
        precision = {}
        for i, field in enumerate(fields):
            if all(type(record[i]) in [int, long] for record in records):
                field_type[field] = 'N' # integers
                precision[field] = 0
            elif all(type(record[i]) in [int, long, float] for record in records):
                field_type[field] = 'N' # numeric
                precision[field] = 5
            else:
                field_type[field] = 'C' # string (characters)
                precision[field] = 0


        # LIST OF LINESTRINGS
        if isinstance(geometry[0], LineString):
            sw = shapefile.Writer(shapefile.POLYLINE)

            # fields
            for field in fields:
                sw.field(field, field_type[field], decimal=precision[field])
            
            if not fields:
                # add dummy length field and prepare records for it
                records = [[line.length] for line in geometry]
                sw.field('length', 'N', decimal=5)

            # geometry and records
            for line, record in itertools.izip(geometry, records):
                sw.line([list(line.coords)])
                sw.record(*record)
                
            sw.save(filename)

        # LIST OF POLYGONS
        elif isinstance(geometry[0], Polygon):
            sw = shapefile.Writer(shapefile.POLYGON)
            
            # fields
            for field in fields:
                sw.field(field, field_type[field], decimal=precision[field])

            # geometry and records
            for polygon, record in itertools.izip(geometry, records):
                sw.poly([list(polygon.exterior.coords)])
                sw.record(*record)
                
            sw.save(filename)
        
        # LIST OF POINTS
        elif isinstance(geometry[0], Point):
            sw = shapefile.Writer(shapefile.POINT)
            
            # fields
            for field in fields:
                sw.field(field, field_type[field], decimal=precision[field])
            
            if not fields:
                # add dummy length field and prepare records for it
                records = [[point.x, point.y] for point in geometry]
                sw.field('x', 'N', decimal=5)
                sw.field('y', 'N', decimal=5)
                
            # shapes and records
            for point, record in itertools.izip(geometry, records):
                sw.point(point.x, point.y)
                sw.record(*record)

            # save
            sw.save(filename)
            
        
        else:
            raise NotImplementedError

    else:
        raise NotImplementedError


