# # from panda3d.core import WindowProperties, loadPrcFileData
# # from direct.showbase.ShowBase import ShowBase
# # import threading
# # import time
# # from robot_simulator import RobotSimulator

# # # Prevent Panda3D from opening its own window
# # loadPrcFileData("", "window-type none")

# # class PandaApp(ShowBase):
# #     def __init__(self, window_id):
# #         ShowBase.__init__(self)

# #         wp = WindowProperties()
# #         wp.setParentWindow(window_id)
# #         wp.setOrigin(0, 0)
# #         wp.setSize(400, 700)

# #         self.makeDefaultPipe()
# #         self.openDefaultWindow(props=wp)

# #         self.setBackgroundColor(0.95, 0.95, 0.95, 1)

# #         # Attach robot simulator
# #         self.sim = RobotSimulator(self)

# #         # Run Panda loop safely
# #         self._running = True
# #         threading.Thread(target=self._loop, daemon=True).start()

# #     def _loop(self):
# #         while self._running:
# #             self.taskMgr.step()
# #             time.sleep(0.01)

# from panda3d.core import WindowProperties, loadPrcFileData
# from direct.showbase.ShowBase import ShowBase
# from robot_simulator import RobotSimulator

# # Prevent Panda from opening its own window
# loadPrcFileData("", "window-type none")

# class PandaApp(ShowBase):
#     def __init__(self, parent_window_id, tk_root):
#         ShowBase.__init__(self)

#         wp = WindowProperties()
#         wp.setParentWindow(parent_window_id)
#         wp.setOrigin(0, 0)
#         wp.setSize(400, 700)

#         self.makeDefaultPipe()
#         self.openDefaultWindow(props=wp)

#         self.setBackgroundColor(0.95, 0.95, 0.95, 1)

#         self.sim = RobotSimulator(self)

#         self.tk_root = tk_root

#         # 🔁 Drive Panda3D from Tkinter (MAIN THREAD)
#         self._step()

#     def _step(self):
#         self.taskMgr.step()
#         self.tk_root.after(10, self._step)


from panda3d.core import WindowProperties, loadPrcFileData
from direct.showbase.ShowBase import ShowBase
from panda.robot_simulator import RobotSimulator

# Prevent Panda3D from opening its own window
loadPrcFileData("", "window-type none")

class PandaApp(ShowBase):
    def __init__(self, parent_window_id, tk_root):
        ShowBase.__init__(self)

        wp = WindowProperties()
        wp.setParentWindow(parent_window_id)
        wp.setOrigin(0, 0)
        wp.setSize(400, 700)

        self.makeDefaultPipe()
        self.openDefaultWindow(props=wp)

        self.setBackgroundColor(0.95, 0.95, 0.95, 1)

        self.sim = RobotSimulator(self)

        self.tk_root = tk_root
        self._step()

    def _step(self):
        self.taskMgr.step()
        self.tk_root.after(10, self._step)
