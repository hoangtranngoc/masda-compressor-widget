import omni.ui as ui
import omni.kit.app
import carb
from omni.ui import color

from .services.data_service import COMPRESSOR_STATUS_EVENT

OK_STYLE={"background_color": color.black, "secondary_color": color.green}
WARNING_STYLE= {"background_color": color.black, "secondary_color": color.yellow}
ALARM_STYLE= {"background_color": color.black, "secondary_color": color.red} 

class WidgetMonitorWindow():

    def __init__(self, ext_id):

        bus = omni.kit.app.get_app().get_message_bus_event_stream()
        self._stage_event_sub = bus.create_subscription_to_pop_by_type(COMPRESSOR_STATUS_EVENT, self.on_event)

        # create UI
        self._window = ui.Window("Gas Compressor Monitor Widget", width=350, height=350)
        with self._window.frame:
            with ui.VStack():
                with ui.HStack():
                    ui.Label("Temperature (C):")
                    self.temperatureSlider = ui.FloatSlider(min=0, max=50, height=20)
                    
                with ui.HStack():
                    ui.Label("Pressure (bar):")
                    self.pressureSlider = ui.FloatSlider(min=0, max=7, height=20)


                with ui.HStack():
                    ui.Label("Flow:")
                    self.flowSlider = ui.FloatSlider(min=0, max=250, height=20)


                with ui.HStack():
                    ui.Label("Power Energy #1 (Kwh):")
                    self.power1Slider = ui.FloatSlider(min=0, max=12, height=20)


                with ui.HStack():
                    ui.Label("Power Energy #2 (Kwh):")
                    self.power2Slider = ui.FloatSlider(min=0, max=12, height=20)

                with ui.HStack():
                    ui.Label("Power Energy #3 (Kwh):")
                    self.power3Slider = ui.FloatSlider(min=0, max=12, height=20)

    
    def on_event(self, e):
        carb.log_warn(f"on_event {e.type}, {e.payload}")
        
        temperature = e.payload["temperature"]
        self._update_ui(temperature, self.temperatureSlider, warning_threshold=25, alarm_threshold=30)

        pressure = e.payload["pressure"]
        self._update_ui(pressure, self.pressureSlider, warning_threshold=4, alarm_threshold=6)

        flow = e.payload["flow"]
        self._update_ui(flow, self.flowSlider, warning_threshold=130, alarm_threshold=200)

        power1 = e.payload["powerEnergy1"]
        self._update_ui(power1, self.power1Slider, warning_threshold=7, alarm_threshold=10)

        power2 = e.payload["powerEnergy2"]
        self._update_ui(power2, self.power2Slider, warning_threshold=7, alarm_threshold=10)

        power3 = e.payload["powerEnergy3"]
        self._update_ui(power3, self.power3Slider, warning_threshold=7, alarm_threshold=10)

    def __del__(self):
        self.destroy()

    def destroy(self):
        self._stage_event_sub = None
        self._window = None
        self.temperatureSlider = None
        self.pressureSlider = None
        self.flowSlider = None
        self.power1Slider = None
        self.power2Slider = None
        self.power3Slider = None

    def _update_ui(self, value, slider, warning_threshold, alarm_threshold):
        slider.model.set_value(value)
        if value < warning_threshold:
            slider.style = OK_STYLE
        elif value < alarm_threshold:
            slider.style = WARNING_STYLE
        else:
            slider.style = ALARM_STYLE
        