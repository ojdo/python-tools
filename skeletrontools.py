from shapely.geometry import Polygon, LineString, Point, box

import Skeletron
import pandashp
import shapely.ops

def select_biggest_polygon_from_multipolygon(multi_polygon):
    """Return the polygon with the biggest exterior length from a multipolygon."""
    if isinstance(multi_polygon, Polygon):
        return multi_polygon

    component_lengths = [poly.exterior.length for poly in multi_polygon]
    biggest_component_index = component_lengths.index(max(component_lengths))
    return multi_polygon[biggest_component_index]


def extract_lines_from_graph(graphs):
    lines = []
    for graph in graphs:
        for line_dict in graph.edge.values():
            if line_dict:
                for k in line_dict.keys():
                    lines.append(line_dict[k]['line'])
    return lines

def skeletonize(roads, buffer_length=60,
                       dissolve_length=30,
                       simplify_length=30,
                       buffer_resolution=2,
                       psg_length=150):
    """Uses qhull to find simplified road network for given DataFrame of roads.
    
    Args:
        roads               pandashp DataFrame of shapely LINESTRINGs (projected)
        buffer_length       optional roughly equivalent to amount of generalization
        dissolve_length     optional (def: 30) considerably smaller than buffer_length
        simplify_length     optional 
        buffer_resolution   optional
        psg_length          optional (default: 150) Skeletron algorithm length
    """

    # buffer and merge streets
    streets_buffered = [way['geometry'].buffer(buffer_length, buffer_resolution) 
                                              for _, way in roads.iterrows()]
    streets_buffered_merged = shapely.ops.cascaded_union(streets_buffered)

    # the union now has several connected components
    # select the component with the longest circumference (=exterior.length)
    # and undo the buffer operation and repeat the selection process
    streets_buffered_merged = select_biggest_polygon_from_multipolygon(streets_buffered_merged)
    streets_buffered_merged = streets_buffered_merged.buffer(-dissolve_length)
    streets_buffered_merged = select_biggest_polygon_from_multipolygon(streets_buffered_merged)
    streets_buffered_merged_simplified = streets_buffered_merged.simplify(simplify_length)

    # then calculate skeleton (expensive but necessary)
    street_graphs = Skeletron.polygon_skeleton_graphs(streets_buffered_merged_simplified,psg_length)
    street_lines = extract_lines_from_graph(street_graphs)

    # merge list of lines to MultiLine
    street_lines_merged = shapely.ops.linemerge(street_lines)

    # intersecting multiline with its bounding box somehow triggers a first
    whole_city = box(*street_lines_merged.bounds)

    # perform linemerge (one linestring between each crossing only)
    # if this fails, write function to perform this on a bbox-grid and then
    # merge the result
    street_lines_merged_intersect = street_lines_merged.intersection(whole_city)
    street_lines_merged_intersect_merged = shapely.ops.linemerge(street_lines_merged_intersect)

    # and remove zigzaging (for smoother plots)
    streets = street_lines_merged_intersect_merged.simplify(simplify_length)
    return streets