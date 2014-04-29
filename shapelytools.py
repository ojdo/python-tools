from shapely.geometry import LineString, MultiPoint, Point, Polygon

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
        list of indices, so that all lines[indices] touch LineString of
    """
    return [k for k, line in enumerate(lines) if line.touches(of)]
    

def bend_towards(line, where, to):
    """Move the point where along a line to the point at locaton to.
    
    Args:
        line: a LineString
        where: a point ON the line (not necessarily a vertex)
        to: a point NOT on the line where the nearest vertex will be moved to
    
    Returns:
        the modified (bent) line 
    """
    
    if not line.contains(where) and not line.touches(where):
        raise ValueError('line does not contain point.')
        
    coords = line.coords[:]
    # easy case: where is (almost) a vertex of line
    for k, vertex in enumerate(coords):
        if where.almost_equals(Point(vertex)):
            # move coordinates of line vertex to destination
            coords[k] = to.coords[0]
            return LineString(coords)
    
    # hard case: where lies between vertices of line, so
    # find nearest vertex and move that one to point to
    _, min_k = min((where.distance(Point(vertex)), k) 
                           for k, vertex in enumerate(coords))
    coords[min_k] = to.coords[0]
    return LineString(coords)


def snappy_endings(lines, max_distance):
    """Snap endpoints of lines together if they are at most max_length away.
    
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
    
    # 
    for endpoint in isolated_endpoints:
        # find all vertices within a radius of max_distance
        target = nearest_neighbor_within(snapping_points, endpoint, max_distance)
        
        # do nothing if no target point to snap to is found
        if not target:
            continue       
        
        # find the LineString to modify within snapped_lines and update it        
        for i, snapped_line in enumerate(snapped_lines):
            if endpoint.touches(snapped_line):
                snapped_lines[i] = bend_towards(snapped_line, where=endpoint, to=target)
                break
        
        # also update the corresponding snapping_points
        for i, snapping_point in enumerate(snapping_points):
            if endpoint.equals(snapping_point):
                snapping_points[i] = target
                break

    # post-processing: remove newly created lines of length 0
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
    """Find endpoints of lines that don't touch another line."""
        
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
    
