from shapely.geometry import (box, LineString, MultiLineString, MultiPoint, 
    Point, Polygon)
import shapely.ops

def endpoints_from_lines(lines):
    """Return list of terminal points from list of LineStrings."""
    
    all_points = []
    for line in lines:
        for i in [0, -1]: # start and end point
            all_points.append(line.coords[i])
    
    unique_points = set(all_points)
    
    return [Point(p) for p in unique_points]
    
def vertices_from_lines(lines):
    """Return list of unique vertices from list of LineStrings."""
    
    vertices = []
    for line in lines:
        vertices.extend(list(line.coords))
    return [Point(p) for p in set(vertices)]


def prune_short_lines(lines, min_length):
    """Remove lines from a LineString DataFrame shorter than min_length.
    
    Deletes all lines from a list of LineStrings or a MultiLineString
    that have a total length of less than min_length. Vertices of touching 
    lines are contracted towards the centroid of the removed line.
    
    Args:
        lines: list of LineStrings or a MultiLineString
        min_length: minimum length of a single LineString to be preserved
        
    Returns:
        the pruned pandas DataFrame
    """   
    pruned_lines = [line for line in lines] # converts MultiLineString to list
    to_prune = []
    
    for i, line in enumerate(pruned_lines):
        if line.length < min_length:
            to_prune.append(i)
            for n in neighbors(pruned_lines, line):
                contact_point = line.intersection(pruned_lines[n])
                pruned_lines[n] = bend_towards(pruned_lines[n], 
                                               where=contact_point,
                                               to=line.centroid)
                
    return [line for i, line in enumerate(pruned_lines) if i not in to_prune] 


def neighbors(lines, of):
    """Find the indices in a list of LineStrings that touch a given LineString.
    
    Args:
        lines: list of LineStrings in which to search for neighbors
        of: the LineString which must be touched
        
    Returns:
        list of indices, so that all lines[indices] touch the LineString of
    """
    return [k for k, line in enumerate(lines) if line.touches(of)]
    

def bend_towards(line, where, to):
    """Move the point where along a line to the point at location to.
    
    Args:
        line: a LineString
        where: a point ON the line (not necessarily a vertex)
        to: a point NOT on the line where the nearest vertex will be moved to
    
    Returns:
        the modified (bent) line 
    """
    
    if not line.contains(where) and not line.touches(where):
        raise ValueError('line does not contain the point where.')
        
    coords = line.coords[:]
    # easy case: where is (within numeric precision) a vertex of line
    for k, vertex in enumerate(coords):
        if where.almost_equals(Point(vertex)):
            # move coordinates of the vertex to destination
            coords[k] = to.coords[0]
            return LineString(coords)
    
    # hard case: where lies between vertices of line, so
    # find nearest vertex and move that one to point to
    _, min_k = min((where.distance(Point(vertex)), k) 
                           for k, vertex in enumerate(coords))
    coords[min_k] = to.coords[0]
    return LineString(coords)


def snappy_endings(lines, max_distance):
    """Snap endpoints of lines together if they are at most max_length apart.
    
    Args:
        lines: a list of LineStrings or a MultiLineString
        max_distance: maximum distance two endpoints may be joined together 
    """
    
    # initialize snapped lines with list of original lines
    # snapping points is a MultiPoint object of all vertices
    snapped_lines = [line for line in lines]
    snapping_points = vertices_from_lines(snapped_lines)
    
    # isolated endpoints are going to snap to the closest vertex
    isolated_endpoints = find_isolated_endpoints(snapped_lines)    
    
    # only move isolated endpoints, one by one
    for endpoint in isolated_endpoints:
        # find all vertices within a radius of max_distance as possible
        target = nearest_neighbor_within(snapping_points, endpoint, 
                                         max_distance)
        
        # do nothing if no target point to snap to is found
        if not target:
            continue       
        
        # find the LineString to modify within snapped_lines and update it        
        for i, snapped_line in enumerate(snapped_lines):
            if endpoint.touches(snapped_line):
                snapped_lines[i] = bend_towards(snapped_line, where=endpoint, 
                                                to=target)
                break
        
        # also update the corresponding snapping_points
        for i, snapping_point in enumerate(snapping_points):
            if endpoint.equals(snapping_point):
                snapping_points[i] = target
                break

    # post-processing: remove any resulting lines of length 0
    snapped_lines = [s for s in snapped_lines if s.length > 0]

    return snapped_lines
    
    
def nearest_neighbor_within(others, point, max_distance):
    """Find nearest point among others up to a maximum distance.
    
    Args:
        others: a list of Points or a MultiPoint
        point: a Point
        max_distance: maximum distance to search for the nearest neighbor
        
    Returns:
        A shapely Point if one is within max_distance, None otherwise
    """
    search_region = point.buffer(max_distance)
    interesting_points = search_region.intersection(MultiPoint(others))
    
    if not interesting_points:
        closest_point = None
    elif isinstance(interesting_points, Point):
        closest_point = interesting_points
    else:            
        distances = [point.distance(ip) for ip in interesting_points
                     if point.distance(ip) > 0]
        closest_point = interesting_points[distances.index(min(distances))]
    
    return closest_point


def find_isolated_endpoints(lines):
    """Find endpoints of lines that don't touch another line.
    
    Args:
        lines: a list of LineStrings or a MultiLineString
        
    Returns:
        A list of line end Points that don't touch any other line of lines
    """
        
    isolated_endpoints = []
    for i, line in enumerate(lines):
        other_lines = lines[:i] + lines[i+1:]
        for q in [0,-1]:
            endpoint = Point(line.coords[q])
            if any(endpoint.touches(another_line) 
                   for another_line in other_lines):
                continue
            else:
                isolated_endpoints.append(endpoint)
    return isolated_endpoints
    
def closest_object(geometries, point):
    """Find the nearest geometry among a list, measured from fixed point.
    
    Args:
        geometries: a list of shapely geometry objects
        point: a shapely Point
       
    Returns:
        Tuple (geom, min_dist, min_index) of the geometry with minimum distance 
        to point, its distance min_dist and the list index of geom, so that
        geom = geometries[min_index].
    """    
    min_dist, min_index = min((point.distance(geom), k) 
                              for (k, geom) in enumerate(geometries))
    
    return geometries[min_index], min_dist, min_index
    
    
def project_point_to_line(point, line_start, line_end):
    """Find nearest point on a straight line, measured from given point.
    
    Args:
        point: a shapely Point object
        line_start: the line starting point as a shapely Point
        line_end: the line end point as a shapely Point
    
    Returns:
        a shapely Point that lies on the straight line closest to point
    
    Source: http://gis.stackexchange.com/a/438/19627
    """
    line_magnitude = line_start.distance(line_end)
    
    u = ((point.x - line_start.x) * (line_end.x - line_start.x) +
         (point.y - line_start.y) * (line_end.y - line_start.y)) \
         / (line_magnitude ** 2)

    # closest point does not fall within the line segment, 
    # take the shorter distance to an endpoint
    if u < 0.00001 or u > 1:
        ix = point.distance(line_start)
        iy = point.distance(line_end)
        if ix > iy:
            return line_end
        else:
            return line_start
    else:
        ix = line_start.x + u * (line_end.x - line_start.x)
        iy = line_start.y + u * (line_end.y - line_start.y)
        return Point([ix, iy])
        
def pairs(lst):
    """Iterate over a list in overlapping pairs.
    
    Args:
        lst: an iterable/list
        
    Returns:
        Yields a pair of consecutive elements (lst[k], lst[k+1]) of lst. Last 
        call yields (lst[-2], lst[-1]).
        
    Example:
        lst = [4, 7, 11, 2]
        pairs(lst) yields (4, 7), (7, 11), (11, 2)
       
    Source:
        http://stackoverflow.com/questions/1257413/1257446#1257446
    """
    i = iter(lst)
    prev = i.next()
    for item in i:
        yield prev, item
        prev = item


def project_point_to_object(point, geometry):
    """Find nearest point in geometry, measured from given point.
    
    Args:
        point: a shapely Point
        geometry: a shapely geometry object (LineString, Polygon)
        
    Returns:
        a shapely Point that lies on geometry closest to point
    """
    from sys import maxint
    nearest_point = None
    min_dist = maxint
    
    if isinstance(geometry, Polygon):
        for seg_start, seg_end in pairs(list(geometry.exterior.coords)):
            line_start = Point(seg_start)
            line_end = Point(seg_end)
        
            intersection_point = project_point_to_line(point, line_start, line_end)
            cur_dist =  point.distance(intersection_point)
        
            if cur_dist < min_dist:
                min_dist = cur_dist
                nearest_point = intersection_point
    
    elif isinstance(geometry, LineString):
        for seg_start, seg_end in pairs(list(geometry.coords)):
            line_start = Point(seg_start)
            line_end = Point(seg_end)
        
            intersection_point = project_point_to_line(point, line_start, line_end)
            cur_dist =  point.distance(intersection_point)
        
            if cur_dist < min_dist:
                min_dist = cur_dist
                nearest_point = intersection_point
    else:
        raise NotImplementedError("project_point_to_object not implemented for"+
                                  " geometry type '" + geometry.type + "'.")
    return nearest_point
    

def one_linestring_per_intersection(lines):
    """ Move line endpoints to intersections of line segments.
    
    Given a list of touching or possibly intersecting LineStrings, return a
    list LineStrings that have their endpoints at all crossings and
    intersecting points and ONLY there.
    
    Args:
        a list of LineStrings or a MultiLineString
        
    Returns:
        a list of LineStrings
    """
    lines_merged = shapely.ops.linemerge(lines)

    # intersecting multiline with its bounding box somehow triggers a first
    bounding_box = box(*lines_merged.bounds)

    # perform linemerge (one linestring between each crossing only)
    # if this fails, write function to perform this on a bbox-grid and then
    # merge the result
    lines_merged = lines_merged.intersection(bounding_box)
    lines_merged = shapely.ops.linemerge(lines_merged)
    return lines_merged


def linemerge(linestrings_or_multilinestrings):
    """ Merge list of LineStrings and/or MultiLineStrings.
    
    Given a list of LineStrings and possibly MultiLineStrings, merge all of
    them to a single MultiLineString.
    
    Args:
        list of LineStrings and/or MultiLineStrings
    
    Returns:
        a merged LineString or MultiLineString
    """
    lines = []
    for line in linestrings_or_multilinestrings:
        if isinstance(line, MultiLineString):
            # line is a multilinestring, so append its components
            lines.extend(line)
        else:
            # line is a line, so simply append it
            lines.append(line)
        
    return shapely.ops.linemerge(lines)
    
