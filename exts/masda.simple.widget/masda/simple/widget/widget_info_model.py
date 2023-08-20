import carb.events
import omni.kit.app
from omni.ui import scene as sc

MY_CUSTOM_EVENT = ""

class WidgetInfoModel(sc.AbstractManipulatorModel):
    """User part. Simple value holder."""

    class TermperatureItem(sc.AbstractManipulatorItem):
        def __init__(self):
            super().__init__()
            self.value = [0]

    def __init__(self):
        super().__init__()
        self.temperature = WidgetInfoModel.TermperatureItem()
        carb.log_warn(f"register custom event:")
        # # App provides common event bus. It is event queue which is popped every update (frame).
        self._bus = omni.kit.app.get_app().get_message_bus_event_stream()
        self._stage_event_sub = self._bus.create_subscription_to_pop_by_type(MY_CUSTOM_EVENT, self._on_event)

    def get_item(self, identifier):
        carb.log_warn(f"get_item: {type(self.temperature)}")
        return self.temperature

    def get_as_floats(self, item):
        carb.log_warn(f"get_as_float: {type(item)}")
        if item == self.temperature:
            return item.value
        return []

    def set_float(self, item, value):
        item.value = value
        self._item_changed(item)

    def _on_event(self, e):
        carb.log_warn(f"Received a event data: {type(e.payload)}")
        item = self.get_item("temperature")
        self.set_float(item, e.payload["data"])

    