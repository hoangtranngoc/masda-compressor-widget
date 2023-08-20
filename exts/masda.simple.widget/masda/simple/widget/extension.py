import omni.ext
import carb
from pxr import Sdf
from .widget_monitor_window import WidgetMonitorWindow
from .widget_simulation_input_window import WidgetSimulationInputWindow
from omni.services.core import main
from .widget_info_scene import WidgetInfoScene
from omni.kit.viewport.utility import get_active_viewport_window
from .gas_simulation import FluidBallEmitterDemo
from omni.usd import get_context
from omni.physx import get_physx_interface


from .services.data_service import router

# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class MasdaSimpleWidgetExtension(omni.ext.IExt):
    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    def on_startup(self, ext_id):
        print("[masda.simple.widget] masda simple widget startup")

        ext_name = ext_id.split("-")[0]
        url_prefix = carb.settings.get_settings_interface().get(f"exts/{ext_name}/url_prefix")

        main.register_router(router=router, prefix=url_prefix, tags=["Gas Compressor Status"])

        self._widget_monitor_window = WidgetMonitorWindow(ext_id)

        self._widget_simulation_input_window = WidgetSimulationInputWindow(ext_id)

        self.stage = get_context().get_stage()

        self.simulation = FluidBallEmitterDemo()
        self.simulation.create(self.stage, False, True)

        self._add_sub_to_update()

    def _add_sub_to_update(self):
        self._update_sub = omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(
            self._on_update, name="omni.physx demo update "
        )

    def _on_update(self, e):
        self.simulation.update(self.stage, e.payload["dt"], None, get_physx_interface())


        # # Get the active (which at startup is the default Viewport)
        # viewport_window = get_active_viewport_window()
        # # Build out the scene
        # self._widget_info_viewport = WidgetInfoScene(viewport_window, ext_id)

        
    def on_shutdown(self):
        print("[masda.simple.widget] masda simple widget shutdown")

        main.deregister_router(router=router)

        if self.simulation:
            self.simulation.on_shutdown() 
            self.simulation = None

        if self._update_sub:
            self._update_sub = None

        if self._widget_monitor_window:
            self._widget_monitor_window.destroy()

        # if self._widget_info_viewport:
        #     self._widget_info_viewport.destroy()
        #     self._widget_info_viewport = None



