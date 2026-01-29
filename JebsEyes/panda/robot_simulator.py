from panda3d.core import DirectionalLight, AmbientLight, LineSegs, LColor, NodePath, GeomNode, GeomVertexFormat, GeomVertexData, GeomVertexWriter, GeomTriangles, Geom, GeomVertexReader
from JebsEyes import geometry

class RobotSimulator:
    def __init__(self, base):
        self.base = base
        self.render = base.render
        self.camera = base.camera

        self.setup_lighting()
        self.create_robot()
        self.setup_camera()
        self.create_grid()

        # 3D ball (This will be initially hidden, as the tennis ball will not be in view yet)
        self.ball_node = geometry.make_sphere(loader=self.base.loader, radius=0.3, color=(0, 1, 0, 1))
        self.ball_node.setPos(0, 5, 0.5)
        self.ball_node.show()
        self.ball_node.reparentTo(self.render)
        self.ball_node.hide() # Hide initially

    def set_ball_position(self, x, y, z=0.5):
        """ Update the 3D ball position in the simulator, and show it. """
        self.ball_node.setPos(x, y, z)
        self.ball_node.show()

    def setup_lighting(self):
        dlight = DirectionalLight("dlight")
        dlight.setColor((1, 1, 1, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(-45, -45, 0)
        self.render.setLight(dlnp)

        ambient = AmbientLight("ambient")
        ambient.setColor((0.4, 0.4, 0.4, 1))
        self.render.setLight(self.render.attachNewNode(ambient))

    def create_robot(self):
        self.robot = self.render.attachNewNode("robot")
        self.robot.setScale(2.0)

        chassis = geometry.cylinder(radius=1.5, height=0.5)
        chassis.reparentTo(self.robot)
        chassis.setZ(0.25)

        self.sensor_pivot = self.robot.attachNewNode("sensor_pivot")
        self.sensor_pivot.setZ(0.8)

        sensor = geometry.cylinder(radius=0.15, height=0.6, color=(1, 0, 0, 1))
        sensor.reparentTo(self.sensor_pivot)
        sensor.setHpr(0, 90, 0)

    def setup_camera(self):
        self.camera.reparentTo(self.render)
        self.camera.setPos(0, -15, 6)
        self.camera.lookAt(self.robot)

    def create_grid(self):
        lines = LineSegs()
        lines.setColor(0.7, 0.7, 0.7, 1)

        for i in range(-20, 21, 2):
            lines.moveTo(i, -20, 0)
            lines.drawTo(i, 20, 0)
            lines.moveTo(-20, i, 0)
            lines.drawTo(20, i, 0)

        grid = self.render.attachNewNode(lines.create())
        grid.setZ(-0.01)

    # 🔜 Hook vision yaw here
    def set_sensor_angle(self, yaw_deg):
        self.sensor_pivot.setH(yaw_deg)
