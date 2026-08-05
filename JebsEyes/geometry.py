
from panda3d.core import NodePath


def make_sphere(loader, radius=1.0, color=(0, 1, 0, 1)):
    """
    Create a sphere using Panda3D's built-in model.
    """
    sphere = loader.loadModel("models/misc/sphere")
    sphere.setScale(radius)
    sphere.setColor(*color)
    return sphere


def cylinder(radius=1, height=1, slices=32, color=(0.4, 0.4, 0.4, 1)):
    # (your existing procedural cylinder code is FINE)
    import math
    from panda3d.core import (
        GeomVertexFormat, GeomVertexData, Geom,
        GeomTriangles, GeomVertexWriter, GeomEnums, GeomNode
    )

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
