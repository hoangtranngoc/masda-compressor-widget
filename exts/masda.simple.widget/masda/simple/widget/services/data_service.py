from omni.services.core import routers
import carb

from pydantic import BaseModel, Field
import omni.kit.commands

COMPRESSOR_STATUS_EVENT = carb.events.type_from_string("masda.simple.widget.COMPRESSOR_STATUS_EVENT")

router = routers.ServiceAPIRouter()

class ARequestModel(BaseModel):

    temperature: float = Field(
        ...,
        title="temperature",
        description="// TODO update",
    )

    pressure: float = Field(
        ...,
        title="pressure",
        description="// TODO update",
    )

    flow: float = Field(
        ...,
        title="flow",
        description="// TODO update",
    )

    powerEnergy1: float = Field(
        ...,
        title="power enegery #1",
        description="// TODO update",
    )

    powerEnergy2: float = Field(
        ...,
        title="power enegery #2",
        description="// TODO update",
    )

    powerEnergy3: float = Field(
        ...,
        title="power enegery #3",
        description="// TODO update",
    )

class AResponseModel(BaseModel):
    
    success: bool = Field(
        False,
        title="status",
    )


@router.post(
    path="/status",
    summary="status of the gas compressor",
    description="temperature, pressure, flow, power enegry",
    response_model=AResponseModel,
)


async def status(request: ARequestModel) -> AResponseModel:

    carb.log_warn(f"Received a request to store gas compressor status (temperature:{request.temperature}, pressure:{request.pressure}) ")

    # stage = omni.usd.get_context().get_stage() 
    # prim = stage.DefinePrim('/SensorData', 'Xform')  
    # attr = prim.CreateAttribute("data", Sdf.ValueTypeNames.String) 
    # attr.Set(str(request.temperature))
    
    bus = omni.kit.app.get_app().get_message_bus_event_stream()
    bus.push(COMPRESSOR_STATUS_EVENT, payload={"temperature": request.temperature, "pressure": request.pressure, "flow": request.flow, "powerEnergy1": request.powerEnergy1, "powerEnergy2": request.powerEnergy2, "powerEnergy3": request.powerEnergy3})

    if request.temperature > 30 or request.pressure > 5:
        omni.kit.commands.execute('BindMaterial',
            material_path='/World/Looks/ABS_Soft_Leather_Pop_Grapefruit',
            prim_path=['/World/Plane'],
            strength=['weakerThanDescendants'])

    else:
        omni.kit.commands.execute('BindMaterial',
            material_path='/World/Looks/ABS_Soft_Woven_Leather_Mint',
            prim_path=['/World/Plane'],
            strength=['weakerThanDescendants'])

    return AResponseModel(
        success=True
    )

        # omni.kit.commands.execute('BindMaterial',
        #     material_path='/World/demo/Looks/Shape_537',
        #     prim_path=['/World/demo/Shape_IndexedFaceSet_032/Shape_IndexedFaceSet_015'],
        #     strength=['weakerThanDescendants'])
        # omni.kit.commands.execute('BindMaterial',
        #     material_path='/World/demo/Looks/Shape_537',
        #     prim_path=['/World/demo/Shape_IndexedFaceSet_024/Shape_IndexedFaceSet_024'],
        #     strength=['weakerThanDescendants'])
        # omni.kit.commands.execute('BindMaterial',
        #     material_path='/World/demo/Looks/Shape_537',
        #     prim_path=['/World/demo/Shape_IndexedFaceSet_25/Shape_IndexedFaceSet_032'],
        #     strength=['weakerThanDescendants'])
        # omni.kit.commands.execute('BindMaterial',
        #     material_path='/World/demo/Looks/Shape_537',
        #     prim_path=['/World/demo/Shape_IndexedFaceSet_25/Shape_IndexedFaceSet_060'],
        #     strength=['weakerThanDescendants'])


