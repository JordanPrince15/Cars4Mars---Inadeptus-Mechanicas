# # from panda3d.core import GeomVertexFormat, GeomVertexData, Geom, GeomNode, GeomTriangles, GeomVertexWriter, GeomEnums, NodePath
# # import math

# # def cylinder(radius = 1, height = 1, slices = 32, color = (0.4, 0.4, 0.4, 1)):

# #     format = GeomVertexFormat.getV3n3c4()
# #     vdata = GeomVertexData("cylinder", format, GeomEnums.UHStatic)

# #     vertex = GeomVertexWriter(vdata, 'vertex')
# #     normal = GeomVertexWriter(vdata, 'normal')
# #     color_writer = GeomVertexWriter(vdata, 'color')
    
    

# #     angle_step = 2 * math.pi / slices

# #     # Keep track of indices
# #     side_indices = []
    

# #     for i in range(slices + 1):
# #         angle = i * angle_step
# #         x = radius * math.cos(angle)
# #         y = radius * math.sin(angle)

# #         # Bottom vertex
# #         vertex.addData3(x, y, -height / 2)
# #         normal.addData3(x, y, 0)
# #         color_writer.addData4f(*color)

# #         # Top vertex
# #         vertex.addData3(x, y, height / 2)
# #         normal.addData3(x, y, 0)
# #         color_writer.addData4f(*color)

# #         # Store vertex indices
# #         side_indices.append((2 * i, 2 * i + 1))
    
# #     # Capping the cylinder
# #         #Top Cap
# #     center_idx = 66  # wrap around
   
    
   
        

# #     # Now build the triangle strip for the sides
# #     tris = GeomTriangles(GeomEnums.UHStatic)
# #     for i in range(slices):
# #         i0b, i0t = side_indices[i]
# #         i1b, i1t = side_indices[i + 1]

# #         # Two triangles per quad
# #         tris.addVertices(i0b, i1b, i1t)
# #         tris.addVertices(i0b, i1t, i0t)
# #         # tris.addVertices(Center_vertex_Top, i, i + 1)
        
# #     for j in range(len(side_indices) - 1):
# #         tris.addVertices(center_idx, side_indices[j], side_indices[j + 1])


# #     geom = Geom(vdata)
# #     geom.addPrimitive(tris)

# #     node = GeomNode("cylinder")
# #     node.addGeom(geom)
# #     return NodePath(node)

# from panda3d.core import GeomVertexFormat, GeomVertexData, Geom, GeomNode, GeomTriangles, GeomVertexWriter, GeomEnums, NodePath
# import math

# def cylinder(radius = 1, height = 1, slices = 32, color = (0.4, 0.4, 0.4, 1)):
#     format = GeomVertexFormat.getV3n3c4()
#     vdata = GeomVertexData("cylinder", format, GeomEnums.UHStatic)

#     vertex = GeomVertexWriter(vdata, 'vertex')
#     normal = GeomVertexWriter(vdata, 'normal')
#     color_writer = GeomVertexWriter(vdata, 'color')
    
#     angle_step = 2 * math.pi / slices

#     # Keep track of indices
#     side_indices = []
    
#     # Generate side vertices
#     for i in range(slices + 1):
#         angle = i * angle_step
#         x = radius * math.cos(angle)
#         y = radius * math.sin(angle)

#         # Bottom vertex
#         vertex.addData3(x, y, -height / 2)
#         normal.addData3(x, y, 0)
#         color_writer.addData4f(*color)

#         # Top vertex
#         vertex.addData3(x, y, height / 2)
#         normal.addData3(x, y, 0)
#         color_writer.addData4f(*color)

#         # Store vertex indices
#         side_indices.append((2 * i, 2 * i + 1))
    
#     # Add center vertices for caps
#     # Bottom center vertex
#     bottom_center_idx = len(side_indices) * 2
#     vertex.addData3(0, 0, -height / 2)
#     normal.addData3(0, 0, -1)  # Pointing downward
#     color_writer.addData4f(*color)
    
#     # Top center vertex
#     top_center_idx = bottom_center_idx + 1
#     vertex.addData3(0, 0, height / 2)
#     normal.addData3(0, 0, 1)  # Pointing upward
#     color_writer.addData4f(*color)
    
#     # Now build the triangle strip for the sides
#     tris = GeomTriangles(GeomEnums.UHStatic)
    
#     # Side triangles
#     for i in range(slices):
#         i0b, i0t = side_indices[i]
#         i1b, i1t = side_indices[i + 1]

#         # Two triangles per quad
#         tris.addVertices(i0b, i1b, i1t)
#         tris.addVertices(i0b, i1t, i0t)
    
#     # Bottom cap triangles
#     for i in range(slices):
#         i0b, _ = side_indices[i]
#         i1b, _ = side_indices[i + 1]
#         tris.addVertices(bottom_center_idx, i1b, i0b)
    
#     # Top cap triangles
#     for i in range(slices):
#         _, i0t = side_indices[i]
#         _, i1t = side_indices[i + 1]
#         tris.addVertices(top_center_idx, i0t, i1t)

#     geom = Geom(vdata)
#     geom.addPrimitive(tris)

#     node = GeomNode("cylinder")
#     node.addGeom(geom)
#     return NodePath(node)

from panda3d.core import (
    GeomVertexFormat, GeomVertexData, Geom, GeomNode,
    GeomTriangles, GeomVertexWriter, GeomEnums, NodePath
)
import math

def cylinder(radius=1, height=1, slices=32, color=(0.4, 0.4, 0.4, 1)):
    format = GeomVertexFormat.getV3n3c4()
    vdata = GeomVertexData("cylinder", format, GeomEnums.UHStatic)

    v = GeomVertexWriter(vdata, "vertex")
    n = GeomVertexWriter(vdata, "normal")
    c = GeomVertexWriter(vdata, "color")

    angle_step = 2 * math.pi / slices
    indices = []

    for i in range(slices + 1):
        angle = i * angle_step
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)

        v.addData3(x, y, -height / 2)
        n.addData3(x, y, 0)
        c.addData4f(*color)

        v.addData3(x, y, height / 2)
        n.addData3(x, y, 0)
        c.addData4f(*color)

        indices.append((2*i, 2*i+1))

    tris = GeomTriangles(GeomEnums.UHStatic)
    for i in range(slices):
        i0b, i0t = indices[i]
        i1b, i1t = indices[i + 1]
        tris.addVertices(i0b, i1b, i1t)
        tris.addVertices(i0b, i1t, i0t)

    geom = Geom(vdata)
    geom.addPrimitive(tris)

    node = GeomNode("cylinder")
    node.addGeom(geom)
    return NodePath(node)
