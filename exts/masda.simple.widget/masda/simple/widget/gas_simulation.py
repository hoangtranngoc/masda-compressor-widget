import math
from pxr import UsdLux, UsdGeom, Sdf, Gf, Vt, UsdPhysics, PhysxSchema
from omni.physx.scripts import utils
from omni.physx.scripts import physicsUtils, particleUtils
import omni.physxdemos as demo
import omni.physx.bindings._physx as physx_settings_bindings
import omni.timeline
import numpy as np
import carb


class FluidBallEmitterDemo(demo.AsyncDemoBase):
    title = "Paint Ball Emitter"
    category = demo.Categories.PARTICLES
    short_description = "PBD particles paint ball emitter"
    description = "Paint-like PBD fluid balls emitted onto a canvas."

    params = {
        "Single_Particle_Set": demo.CheckboxParam(True),
        "Use_Instancer": demo.CheckboxParam(True),
    }

    kit_settings = {
        "persistent/app/viewport/displayOptions": demo.get_viewport_minimal_display_options_int(),
        physx_settings_bindings.SETTING_MIN_FRAME_RATE: 60,
        physx_settings_bindings.SETTING_UPDATE_VELOCITIES_TO_USD: True,
        "rtx/post/aa/op": 3,
        "rtx/post/dlss/execMode": 0,
    }

    def __init__(self):
        super().__init__(enable_flatcache=False, enable_tensor_api=False)
        self._time = 0
        self._is_running = False
        self._rng_seed = 42
        self._rng = np.random.default_rng(self._rng_seed)
        self._ball_spawn_interval = 0.4
        self._next_ball_time = self._ball_spawn_interval
        self._num_balls = 0
        self._num_balls_to_spawn = 1000
        self._num_colors = 20

    def particle_sphere(self, radius, particleSpacing):
        points = []
        dim = math.ceil(2 * radius / particleSpacing)
        for i in range(dim):
            for j in range(dim):
                for k in range(dim):
                    x = i * particleSpacing - radius + self._rng.uniform(-0.05, 0.05)
                    y = j * particleSpacing - radius + self._rng.uniform(-0.05, 0.05)
                    z = k * particleSpacing - radius + self._rng.uniform(-0.05, 0.05)

                    d2 = x * x + y * y + z * z
                    if d2 < radius * radius:
                        points.append(Gf.Vec3f(x, y, z))

        return points

    def set_initial_camera(self, stage, position, target):
        customLayerData = {
            "cameraSettings": {
                "Perspective": {"position": position, "radius": 500, "target": target},
                "boundCamera": "/OmniverseKit_Persp",
            }
        }
        stage.GetRootLayer().customLayerData = customLayerData

    def create_colors(self):

        fractions = np.linspace(0.0, 1.0, self._num_colors)
        colors = []

        for frac in fractions:
            colors.append(self.create_color(frac))

        return colors

    def create_color(self, frac):

        # HSL to RGB conversion
        hue = frac
        saturation = 1.0
        luminosity = 0.5

        hue6 = hue * 6.0
        modulo = Gf.Vec3f((hue6 + 0.0) % 6.0, (hue6 + 4.0) % 6.0, (hue6 + 2.0) % 6.0)
        absolute = Gf.Vec3f(abs(modulo[0] - 3.0), abs(modulo[1] - 3.0), abs(modulo[2] - 3.0))
        rgb = Gf.Vec3f(
            Gf.Clampf(absolute[0] - 1.0, 0.0, 1.0),
            Gf.Clampf(absolute[1] - 1.0, 0.0, 1.0),
            Gf.Clampf(absolute[2] - 1.0, 0.0, 1.0),
        )

        linter = Gf.Vec3f(1.0) * (1.0 - saturation) + rgb * saturation
        rgb = luminosity * linter

        return rgb

    def create_ball(self, stage, pos):

        basePos = Gf.Vec3f(11.0, 12.0, 7.0) + pos

        positions_list = [x + basePos for x in self.ball]
        velocities_list = [Gf.Vec3f(10, 10, 0.0)] * len(positions_list)
        color = Vt.Vec3fArray([self.colors[self._num_balls % self._num_colors]])

        particlePointsPath = Sdf.Path("/particles" + str(self._num_balls))

        if self.usePointInstancer:
            particlePrim = particleUtils.add_physx_particleset_pointinstancer(
                stage,
                particlePointsPath,
                positions_list,
                velocities_list,
                self.particleSystemPath,
                self_collision=True,
                fluid=True,
                particle_group=0,
                particle_mass=0.001,
                density=0.0,
            )

            prototypeStr = str(particlePointsPath) + "/particlePrototype0"
            gprim = UsdGeom.Sphere.Define(stage, Sdf.Path(prototypeStr))
            gprim.CreateDisplayColorAttr(color)
            gprim.CreateRadiusAttr().Set(self.fluid_rest_offset)
        else:
            particlePrim = particleUtils.add_physx_particleset_points(
                stage,
                particlePointsPath,
                positions_list,
                velocities_list,
                [2*self.fluid_rest_offset]*len(positions_list),
                self.particleSystemPath,
                self_collision=True,
                fluid=True,
                particle_group=0,
                particle_mass=0.001,
                density=0.0
            )

            particlePrim.CreateDisplayColorAttr(color)

        self.particlePrims.append(particlePrim)

    @staticmethod
    def extend_array_attribute(attribute, elements):
        array_elements = list(attribute.Get())
        array_elements.extend(elements)
        attribute.Set(array_elements)

    def create_ball_shared(self, stage, pos):

        basePos = Gf.Vec3f(11.0, 12.0, 7.0) + pos
        colorIndex = self._num_balls % self._num_colors
        positions_list = [x + basePos for x in self.ball]
        velocities_list = [Gf.Vec3f(10, 10, 0.0)] * len(positions_list)

        particleSet = PhysxSchema.PhysxParticleSetAPI(self.sharedParticlePrim)
        pointInstancer = UsdGeom.PointInstancer(self.sharedParticlePrim)
        points = UsdGeom.Points(self.sharedParticlePrim)

        #update sim positions first, create attribute as needed.
        #this bocks physics update when changing gfx positions
        if self.useSmoothing:
            simPointsAttr = particleSet.GetSimulationPointsAttr()
            if not simPointsAttr.HasAuthoredValue():
                simPointsAttr.Set(Vt.Vec3fArray([]))
            self.extend_array_attribute(simPointsAttr, positions_list)

        if pointInstancer:
            self.extend_array_attribute(pointInstancer.GetPositionsAttr(), positions_list)
            self.extend_array_attribute(pointInstancer.GetVelocitiesAttr(), velocities_list)
            self.extend_array_attribute(pointInstancer.GetProtoIndicesAttr(), [colorIndex]*len(positions_list))
            self.extend_array_attribute(pointInstancer.GetOrientationsAttr(), [Gf.Quath(1.0, 0.0, 0.0, 0.0)]*len(positions_list))
            self.extend_array_attribute(pointInstancer.GetScalesAttr(), [Gf.Vec3f(1.0)]*len(positions_list))
        elif points:
            self.extend_array_attribute(points.GetPointsAttr(), positions_list)
            self.extend_array_attribute(points.GetVelocitiesAttr(), velocities_list)
            self.extend_array_attribute(points.GetWidthsAttr(), [2*self.fluid_rest_offset]*len(positions_list))
            primVars = points.GetDisplayColorPrimvar()
            primVarsIndicesAttr = primVars.GetIndicesAttr()
            #indices = list(primVarsIndicesAttr.Get())
            self.extend_array_attribute(primVarsIndicesAttr, [colorIndex]*len(positions_list))


    def create(self, stage, Single_Particle_Set, Use_Instancer):
        carb.log_warn(f"create simulation")
        self._setup_callbacks()
        self.stage = stage

        self.useSharedParticleSet = Single_Particle_Set
        self.usePointInstancer = Use_Instancer
        self.useSmoothing = True
        self.useAnisotropy = True

        # set up axis to z
        # UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        # UsdGeom.SetStageMetersPerUnit(stage, 1)

        self.set_initial_camera(
            self.stage,
            Gf.Vec3d(58.977283027096256, -5.269442757147381, 30.051278140695423),
            Gf.Vec3d(3.56411508564279, 43.06188053546666, -14.596946991744531),
        )

        distantLight = UsdLux.DistantLight.Define(stage, Sdf.Path("/DistantLight"))
        distantLight.CreateIntensityAttr(1500)
        distantLight.CreateAngleAttr(0.53)

        # Physics scene
        scenePath = Sdf.Path("/physicsScene")
        scene = UsdPhysics.Scene.Define(stage, scenePath)
        scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
        scene.CreateGravityMagnitudeAttr().Set(9.81)

        # Particle System
        particleSystemPath = Sdf.Path("/particleSystem0")
        self.particleSystemPath = particleSystemPath
        carb.log_warn(particleSystemPath) 

        particleSpacing = 0.18
        restOffset = particleSpacing * 0.9
        solidRestOffset = restOffset
        fluidRestOffset = restOffset * 0.6
        particleContactOffset = max(solidRestOffset + 0.005, fluidRestOffset / 0.6)
        contactOffset = restOffset + 0.005

        self.fluid_rest_offset = fluidRestOffset

        particle_system = particleUtils.add_physx_particle_system(
            stage,
            particleSystemPath,
            contact_offset=contactOffset,
            rest_offset=restOffset,
            particle_contact_offset=particleContactOffset,
            solid_rest_offset=solidRestOffset,
            fluid_rest_offset=fluidRestOffset,
            solver_position_iterations=4,
            simulation_owner=scenePath,
            max_neighborhood=96
        )

        if self.useSmoothing:
            particleUtils.add_physx_particle_smoothing(
                stage,
                particleSystemPath,
                strength=1.0
            )

        if self.usePointInstancer and self.useAnisotropy:
            particleUtils.add_physx_particle_anisotropy(
                stage,
                particleSystemPath,
                scale=1.0,
            )

        # Create a pbd particle material and set it on the particle system
        pbd_particle_material_path = omni.usd.get_stage_next_free_path(stage, "/pbdParticleMaterial", True)
        particleUtils.add_pbd_particle_material(
            stage,
            pbd_particle_material_path,
            cohesion=5,
            viscosity=100,
            surface_tension=0.0074,
            friction=250,
            damping=0.0,
        )
        physicsUtils.add_physics_material_to_prim(stage, particle_system.GetPrim(), pbd_particle_material_path)

        physicsUtils.add_ground_plane(stage, "/groundPlane", "Z", 100.0, Gf.Vec3f(0.0), Gf.Vec3f(0.5))

        # create particle posititions for a ball filled with particles
        self.ball = self.particle_sphere(1.0, fluidRestOffset * 2)
        self.particlePrims = []
        self.colors = self.create_colors()

        if self.useSharedParticleSet:
            particlePointsPath = Sdf.Path("/particles")

            if self.usePointInstancer:
                self.sharedParticlePrim = particleUtils.add_physx_particleset_pointinstancer(
                    stage,
                    particlePointsPath,
                    [],
                    [],
                    self.particleSystemPath,
                    self_collision=True,
                    fluid=True,
                    particle_group=0,
                    particle_mass=0.001,
                    density=0.0,
                    num_prototypes=0,
                )

                for i, c in enumerate(self.colors):
                    color = Vt.Vec3fArray([c])
                    prototypeStr = str(particlePointsPath) + "/particlePrototype" + str(i)
                    gprim = UsdGeom.Sphere.Define(stage, Sdf.Path(prototypeStr))
                    gprim.CreateDisplayColorAttr(color)
                    gprim.CreateRadiusAttr().Set(self.fluid_rest_offset)
                    pointInstancer = UsdGeom.PointInstancer(self.sharedParticlePrim)
                    pointInstancer.GetPrototypesRel().AddTarget(Sdf.Path(prototypeStr))

            else:
                self.sharedParticlePrim = particleUtils.add_physx_particleset_points(
                    stage,
                    particlePointsPath,
                    [],
                    [],
                    [],
                    self.particleSystemPath,
                    self_collision=True,
                    fluid=True,
                    particle_group=0,
                    particle_mass=0.001,
                    density=0.0,
                )

                #unfortunately display color primvar with "vertex" interpolation doesn't seem to work on UsdGeomPoints yet.
                self.sharedParticlePrim.CreateDisplayColorAttr().Set(self.colors)
                self.sharedParticlePrim.CreateDisplayColorPrimvar(interpolation="vertex")
                self.sharedParticlePrim.GetDisplayColorPrimvar().CreateIndicesAttr().Set([])

            maxParticles = self._num_balls_to_spawn*len(self.ball)
            self.sharedParticlePrim.GetPrim().CreateAttribute("physxParticle:maxParticles", Sdf.ValueTypeNames.Int).Set(maxParticles)
            self.particlePrims.append(self.sharedParticlePrim)
        else:
            self.sharedParticlePrim = None

    def on_simulation_event(self, e):
        carb.log_warn(f"on_simulation_event {e.type}")
        if e.type == int(physx_settings_bindings.SimulationEvent.STOPPED):
            if self.stage:
                #particles in self.sharedParticlePrim are reset by integration reset code
                if self.sharedParticlePrim:
                    pointInstancer = UsdGeom.PointInstancer(self.sharedParticlePrim)
                    points = UsdGeom.Points(self.sharedParticlePrim)
                    if pointInstancer:
                        pointInstancer.GetProtoIndicesAttr().Set(Vt.IntArray())
                    elif points:
                        points.GetDisplayColorPrimvar().GetIndicesAttr().Set([])
                else:
                    for prim in self.particlePrims:
                        self.stage.RemovePrim(prim.GetPath())

    def on_timeline_event(self, e):
        carb.log_warn(f"on_timeline_event {e.type}")
        if e.type == int(omni.timeline.TimelineEventType.STOP):
            self._is_running = False
            self._rng = np.random.default_rng(self._rng_seed)
            self._num_balls = 0
            self._time = 0
            self._next_ball_time = self._ball_spawn_interval
        if e.type == int(omni.timeline.TimelineEventType.PAUSE):
            self._is_running = False
        elif e.type == int(omni.timeline.TimelineEventType.PLAY):
            self._is_running = True

    def on_physics_step(self, dt):
        carb.log_warn(f"on_physics_step")
        self._time += dt

    def update(self, stage, dt, viewport, physxIFace):
        if not self._is_running:
            return

        carb.log_warn(f"_num_balls {self._num_balls}")
        if self._num_balls >= self._num_balls_to_spawn:
            return

        carb.log_warn(f"_next_ball_time {self._next_ball_time}")
        if self._time < self._next_ball_time:
            return

        self._next_ball_time = self._time + self._ball_spawn_interval

        self._num_balls += 1
        x = self._rng.uniform(-8, 8)
        y = self._rng.uniform(-8, 8)
        pos = Gf.Vec3f(x, y, 0.0)

        if self.sharedParticlePrim:
            self.create_ball_shared(self.stage, pos)
        else:
            self.create_ball(self.stage, pos)

