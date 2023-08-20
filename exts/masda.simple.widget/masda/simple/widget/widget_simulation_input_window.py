import omni.ui as ui
import omni.kit.app
import carb
from omni.ui import color


class WidgetSimulationInputWindow():

    def __init__(self, ext_id):

        # create UI
        self._window = ui.Window("Gas Compressor Simulation Input", width=300, height=350)
        with self._window.frame:
            with ui.VStack():
                with ui.HStack():
                    ui.Label("Valve 1:")
                    self.valveBox1 = ui.CheckBox()
                    
                with ui.HStack():
                    ui.Label("Valve 2:")
                    self.valveBox2 = ui.CheckBox()

                with ui.HStack():
                    ui.Label("Valve 3:")
                    self.valveBox3 = ui.CheckBox()

                with ui.HStack():
                    ui.Label("Valve 4:")
                    self.valveBox4 = ui.CheckBox()

                with ui.HStack():
                    ui.Label("Valve 5:")
                    self.valveBox5 = ui.CheckBox()

                with ui.HStack():
                    ui.Label("Machine 1:")
                    self.machineBox1 = ui.CheckBox()
                
                with ui.HStack():
                    ui.Label("Machine 2:")
                    self.machineBox2 = ui.CheckBox()

                with ui.HStack():
                    ui.Label("Machine 3:")
                    self.machineBox3 = ui.CheckBox()
                    


    def __del__(self):
        self.destroy()

    def destroy(self):
        self._stage_event_sub = None
        self._window = None


        