from shapely.geometry import LineString, Point, Polygon

def endpoints_from_lines(lines):
    """Return list of terminal points from list of LineStrings."""
    
    all_points = []
    for line in lines:
        all_points.append(line.coords[0])
        all_points.append(line.coords[-1])
    
    unique_points = set(all_points)
    
    return [Point(p) for p in unique_points]