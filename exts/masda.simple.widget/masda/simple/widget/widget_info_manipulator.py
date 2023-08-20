from omni.ui import color as cl
from omni.ui import scene as sc
import omni.ui as ui
import carb.events

class WidgetInfoManipulator(sc.Manipulator):
    """Manipulator that ..."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.destroy()

    def on_build(self):
        self._root = sc.Transform(visible=True)
        with self._root:
            with sc.Transform(scale_to=sc.Space.SCREEN):
                with sc.Transform(transform=sc.Matrix44.get_translation_matrix(800, 800, 0)):
                    with sc.Transform(look_at=sc.Transform.LookAt.CAMERA):
                        self._widget = sc.Widget(500, 150, update_policy=sc.Widget.UpdatePolicy.ON_DEMAND)
                        self._widget.frame.set_build_fn(self.on_build_widgets)

    def on_build_widgets(self):
        with ui.ZStack():
            ui.Rectangle(style={
                "background_color": cl(0.2),
                "border_color": cl(0.7),
                "border_width": 2,
                "border_radius": 4,
            })
            self._name_label = ui.Label("Tempa: ", height=0, alignment=ui.Alignment.LEFT_CENTER)


    def on_model_updated(self, item):
        carb.log_warn(f"on_model_updated: {type(item)}")

        value = self.model.get_as_floats(item)
        carb.log_warn(f"on_model_updated: {type(value)}")

        self._root.transform = sc.Matrix44.get_translation_matrix(0, 0, 0)
        self._root.visible = True
        self._name_label.text = "Temperature:"
        
        self.invalidate()

    def destroy(self):
        self._root = None
        self._name_label = None
