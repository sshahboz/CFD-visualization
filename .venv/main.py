import os
from trame.app import get_server
from trame.ui.vuetify import SinglePageWithDrawerLayout
from trame.widgets import vtk, vuetify
from trame.widgets.vtk import VtkRemoteLocalView
from trame.widgets.vuetify import VTreeview
import trame
from vtkmodules.vtkFiltersSources import vtkProgrammableSource
from trame_vtk.modules.vtk.serializers import configure_serializer
from vtkmodules.vtkCommonDataModel import vtkDataObject
from vtkmodules.vtkFiltersCore import vtkContourFilter
from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridReader
from vtkmodules.vtkRenderingAnnotation import vtkCubeAxesActor
from vtkmodules.vtkFiltersSources import vtkCylinderSource
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkFiltersGeneral import vtkVertexGlyphFilter
from vtkmodules.vtkFiltersGeneral import vtkTransformPolyDataFilter
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkPolyData
from vtkmodules.vtkRenderingCore import vtkPolyDataMapper
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkDataSetMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleSwitch
import vtkmodules.vtkRenderingOpenGL2
import csv
import vtkmodules.vtkCommonDataModel as vtkCommonDataModel
from vtkmodules.vtkCommonCore import vtkPoints, vtkFloatArray
from vtkmodules.vtkCommonDataModel import vtkPolyData
from vtkmodules.vtkFiltersSources import vtkProgrammableSource

source = vtkProgrammableSource()

def load_data():
    output = source.GetPolyDataOutput()
    output.ShallowCopy(polydata)

source.SetExecuteMethod(load_data)

def load_csv_as_polydata(csv_path):
    import csv
    points = vtkPoints()
    dataset_array = vtkFloatArray()
    dataset_array.SetName("Temperature")

    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                x = float(row['Particle X-Coordinate X Particle ID (Study 01 - Particles) [m]'])*100000
                y = float(row['Particle Y-Coordinate X Particle ID (Study 01 - Particles) [m]'])*100000
                z = float(row['Particle Z-Coordinate X Particle ID (Study 01 - Particles) [m]'])*100000
                temp = float(row['Temperature X Particle ID (Study 01 - Particles) [degC]'])
                points.InsertNextPoint(x, y, z)
                dataset_array.InsertNextValue(temp)
            except ValueError:
                continue

    polydata = vtkPolyData()
    polydata.SetPoints(points)
    polydata.GetPointData().SetScalars(dataset_array)
    return polydata

polydata = load_csv_as_polydata("100um.csv")
print("Loaded points:", polydata.GetNumberOfPoints())

# Use Glyph Filter
glyph_filter = vtkVertexGlyphFilter()
glyph_filter.SetInputData(polydata)
glyph_filter.Update()

# Mapper with Glyph output
mapper = vtkPolyDataMapper()
mapper.SetInputConnection(glyph_filter.GetOutputPort())
mapper.SetScalarVisibility(True)
mapper.SelectColorArray("Temperature")
mapper.SetScalarModeToUsePointFieldData()
temperature_range = polydata.GetPointData().GetScalars().GetRange()
mapper.SetScalarRange(temperature_range)


# Actor
actor = vtkActor()
actor.SetMapper(mapper)
actor.GetProperty().SetPointSize(5)



tank = vtkCylinderSource()
tank.SetRadius(8000)
tank.SetHeight(9000)
tank.SetResolution(100)
tank.CappingOff()

# Move the tank center to match particles (Y ~ halfway up)
transform = vtkTransform()
transform.Translate(0, 4500, 0)

transform_filter = vtkTransformPolyDataFilter()
transform_filter.SetInputConnection(tank.GetOutputPort())
transform_filter.SetTransform(transform)
transform_filter.Update()

tank_mapper = vtkPolyDataMapper()
tank_mapper.SetInputConnection(transform_filter.GetOutputPort())

tank_actor = vtkActor()
tank_actor.SetMapper(tank_mapper)
tank_actor.GetProperty().SetColor(0.7, 0.7, 0.7)
tank_actor.GetProperty().SetOpacity(0.2)

renderer = vtkRenderer()
renderer.AddActor(actor)
renderer.AddActor(tank_actor)
renderer.ResetCamera()
camera = renderer.GetActiveCamera()
bounds = polydata.GetBounds()

center = [
    (bounds[0] + bounds[1]) / 2,
    (bounds[2] + bounds[3]) / 2,
    (bounds[4] + bounds[5]) / 2
]
distance = max(bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4]) * 2

camera.SetFocalPoint(center)
camera.SetPosition(center[0], center[1], center[2] + distance)
camera.SetViewUp(0, 1, 0)
renderer.ResetCameraClippingRange()

renderWindow = vtkRenderWindow()
renderWindow.AddRenderer(renderer)

print("Loaded points:", polydata.GetNumberOfPoints())
print("Actors in renderer:", renderer.GetActors().GetNumberOfItems())

# Configure scene encoder
configure_serializer(encode_lut=True, skip_light=True)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------


class Representation:
    Points = 0
    Wireframe = 1
    Surface = 2
    SurfaceWithEdges = 3


class LookupTable:
    Rainbow = 0
    Inverted_Rainbow = 1
    Greyscale = 2
    Inverted_Greyscale = 3


# -----------------------------------------------------------------------------
# VTK pipeline
# -----------------------------------------------------------------------------


renderer.ResetCamera()
renderWindow.Render()


renderWindowInteractor = vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)
renderWindowInteractor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()

# Read Data
csv_path = os.path.join("100um.csv")
polydata = load_csv_as_polydata(csv_path)
print("Number of points:", polydata.GetNumberOfPoints())
print("Bounds:", polydata.GetBounds())



# Extract Array/Field information
fields = [
    (polydata.GetPointData(), vtkDataObject.FIELD_ASSOCIATION_POINTS),
    (polydata.GetCellData(), vtkDataObject.FIELD_ASSOCIATION_CELLS),
]

dataset_array = []

for field, association in fields:
    for i in range(field.GetNumberOfArrays()):
        array = field.GetArray(i)
        if array is None:
            continue
        array_range = array.GetRange()
        dataset_array.append(
            {
                "text": array.GetName(),
                "value": i,
                "range": list(array_range),
                "type": association,
            }
        )
default_array = dataset_array[0]
default_min, default_max = default_array.get("range")

# Mesh
mesh_mapper = vtkPolyDataMapper()
mesh_mapper.SetInputConnection(source.GetOutputPort())
mesh_mapper.SetScalarVisibility(False)
mesh_actor = vtkActor()
mesh_actor.SetMapper(mesh_mapper)
renderer.AddActor(mesh_actor)

# Mesh: Setup default representation to surface
mesh_actor.GetProperty().SetRepresentationToSurface()
mesh_actor.GetProperty().SetPointSize(10)
mesh_actor.GetProperty().EdgeVisibilityOff()
mesh_actor.GetProperty().SetOpacity(1.0)
mesh_actor.GetProperty().SetColor(1, 1, 1)  # white


# Mesh: Apply rainbow color map
mesh_lut = mesh_mapper.GetLookupTable()
mesh_lut.SetHueRange(0.666, 0.0)
mesh_lut.SetSaturationRange(1.0, 1.0)
mesh_lut.SetValueRange(1.0, 1.0)
mesh_lut.Build()

# Mesh: Color by default array
mesh_mapper.SelectColorArray(default_array.get("text"))
mesh_mapper.GetLookupTable().SetRange(default_min, default_max)
if default_array.get("type") == vtkDataObject.FIELD_ASSOCIATION_POINTS:
    mesh_mapper.SetScalarModeToUsePointFieldData()
else:
    mesh_mapper.SetScalarModeToUseCellFieldData()
mesh_mapper.SetScalarVisibility(True)
mesh_mapper.SetUseLookupTableScalarRange(True)

# Contour
contour = vtkContourFilter()
contour.SetInputConnection(source.GetOutputPort())
contour_mapper = vtkDataSetMapper()
contour_mapper.SetInputConnection(contour.GetOutputPort())
contour_actor = vtkActor()
contour_actor.SetMapper(contour_mapper)
renderer.AddActor(contour_actor)

# Contour: ContourBy default array
contour_value = 0.5 * (default_max + default_min)
contour.SetInputArrayToProcess(
    0, 0, 0, default_array.get("type"), default_array.get("text")
)
contour.SetValue(0, contour_value)

# Contour: Setup default representation to surface
contour_actor.GetProperty().SetRepresentationToSurface()
contour_actor.GetProperty().SetPointSize(1)
contour_actor.GetProperty().EdgeVisibilityOff()

# Contour: Apply rainbow color map
contour_lut = contour_mapper.GetLookupTable()
contour_lut.SetHueRange(0.666, 0.0)
contour_lut.SetSaturationRange(1.0, 1.0)
contour_lut.SetValueRange(1.0, 1.0)
contour_lut.Build()

# Contour: Color by default array
contour_mapper.SelectColorArray(default_array.get("text"))
contour_mapper.GetLookupTable().SetRange(default_min, default_max)
if default_array.get("type") == vtkDataObject.FIELD_ASSOCIATION_POINTS:
    contour_mapper.SetScalarModeToUsePointFieldData()
else:
    contour_mapper.SetScalarModeToUseCellFieldData()
contour_mapper.SetScalarVisibility(True)
contour_mapper.SetUseLookupTableScalarRange(True)

# Cube Axes
cube_axes = vtkCubeAxesActor()
renderer.AddActor(cube_axes)

# Cube Axes: Boundaries, camera, and styling
cube_axes.SetBounds(mesh_actor.GetBounds())
cube_axes.SetCamera(renderer.GetActiveCamera())
cube_axes.SetXLabelFormat("%6.1f")
cube_axes.SetYLabelFormat("%6.1f")
cube_axes.SetZLabelFormat("%6.1f")
cube_axes.SetFlyModeToOuterEdges()

renderer.ResetCamera()

# -----------------------------------------------------------------------------
# Trame setup
# -----------------------------------------------------------------------------

server = get_server(client_type="vue2")
state, ctrl = server.state, server.controller

state.setdefault("active_ui", None)

with SinglePageWithDrawerLayout(server) as layout:
    layout.title.set_text("CSV Point Visualizer")

    with layout.toolbar:
        vuetify.VSpacer()
        with vuetify.VBtn(icon=True, click=ctrl.view_reset_camera):
            vuetify.VIcon("mdi-crop-free")

    with layout.content:
        with vuetify.VContainer(fluid=True, classes="pa-0 fill-height", style="background-color: transparent;"):
            view = vtk.VtkRemoteLocalView(renderWindow, namespace="view", mode="local", interactive_ratio=1, style="background-color: transparent;")
            ctrl.view_update = view.update
            ctrl.view_reset_camera = view.reset_camera

# -----------------------------------------------------------------------------
# Callbacks
# -----------------------------------------------------------------------------


@state.change("cube_axes_visibility")
def update_cube_axes_visibility(cube_axes_visibility, **kwargs):
    cube_axes.SetVisibility(cube_axes_visibility)
    ctrl.view_update()


# Selection Change
def actives_change(ids):
    _id = ids[0]
    if _id == "1":  # Mesh
        state.active_ui = "mesh"
    elif _id == "2":  # Contour
        state.active_ui = "contour"
    else:
        state.active_ui = "nothing"


# Visibility Change
def visibility_change(event):
    _id = event["id"]
    _visibility = event["visible"]

    if _id == "1":  # Mesh
        mesh_actor.SetVisibility(_visibility)
    elif _id == "2":  # Contour
        contour_actor.SetVisibility(_visibility)
    ctrl.view_update()


# Representation Callbacks
def update_representation(actor, mode):
    property = actor.GetProperty()
    if mode == Representation.Points:
        property.SetRepresentationToPoints()
        property.SetPointSize(5)
        property.EdgeVisibilityOff()
    elif mode == Representation.Wireframe:
        property.SetRepresentationToWireframe()
        property.SetPointSize(1)
        property.EdgeVisibilityOff()
    elif mode == Representation.Surface:
        property.SetRepresentationToSurface()
        property.SetPointSize(1)
        property.EdgeVisibilityOff()
    elif mode == Representation.SurfaceWithEdges:
        property.SetRepresentationToSurface()
        property.SetPointSize(1)
        property.EdgeVisibilityOn()


@state.change("mesh_representation")
def update_mesh_representation(mesh_representation, **kwargs):
    update_representation(mesh_actor, mesh_representation)
    ctrl.view_update()


@state.change("contour_representation")
def update_contour_representation(contour_representation, **kwargs):
    update_representation(contour_actor, contour_representation)
    ctrl.view_update()


# Color By Callbacks
def color_by_array(actor, array):
    _min, _max = array.get("range")
    mapper = actor.GetMapper()
    mapper.SelectColorArray(array.get("text"))
    mapper.GetLookupTable().SetRange(_min, _max)
    if array.get("type") == vtkDataObject.FIELD_ASSOCIATION_POINTS:
        mesh_mapper.SetScalarModeToUsePointFieldData()
    else:
        mesh_mapper.SetScalarModeToUseCellFieldData()
    mapper.SetScalarVisibility(True)
    mapper.SetUseLookupTableScalarRange(True)


@state.change("mesh_color_array_idx")
def update_mesh_color_by_name(mesh_color_array_idx, **kwargs):
    array = dataset_array[mesh_color_array_idx]
    color_by_array(mesh_actor, array)
    ctrl.view_update()


@state.change("contour_color_array_idx")
def update_contour_color_by_name(contour_color_array_idx, **kwargs):
    array = dataset_array[contour_color_array_idx]
    color_by_array(contour_actor, array)
    ctrl.view_update()


# Color Map Callbacks
def use_preset(actor, preset):
    lut = actor.GetMapper().GetLookupTable()
    if preset == LookupTable.Rainbow:
        lut.SetHueRange(0.666, 0.0)
        lut.SetSaturationRange(1.0, 1.0)
        lut.SetValueRange(1.0, 1.0)
    elif preset == LookupTable.Inverted_Rainbow:
        lut.SetHueRange(0.0, 0.666)
        lut.SetSaturationRange(1.0, 1.0)
        lut.SetValueRange(1.0, 1.0)
    elif preset == LookupTable.Greyscale:
        lut.SetHueRange(0.0, 0.0)
        lut.SetSaturationRange(0.0, 0.0)
        lut.SetValueRange(0.0, 1.0)
    elif preset == LookupTable.Inverted_Greyscale:
        lut.SetHueRange(0.0, 0.666)
        lut.SetSaturationRange(0.0, 0.0)
        lut.SetValueRange(1.0, 0.0)
    lut.Build()


@state.change("mesh_color_preset")
def update_mesh_color_preset(mesh_color_preset, **kwargs):
    use_preset(mesh_actor, mesh_color_preset)
    ctrl.view_update()


@state.change("contour_color_preset")
def update_contour_color_preset(contour_color_preset, **kwargs):
    use_preset(contour_actor, contour_color_preset)
    ctrl.view_update()


# Opacity Callbacks
@state.change("mesh_opacity")
def update_mesh_opacity(mesh_opacity, **kwargs):
    mesh_actor.GetProperty().SetOpacity(mesh_opacity)
    ctrl.view_update()


@state.change("contour_opacity")
def update_contour_opacity(contour_opacity, **kwargs):
    contour_actor.GetProperty().SetOpacity(contour_opacity)
    ctrl.view_update()


# Contour Callbacks
@state.change("contour_by_array_idx")
def update_contour_by(contour_by_array_idx, **kwargs):
    array = dataset_array[contour_by_array_idx]
    contour_min, contour_max = array.get("range")
    contour_step = 0.01 * (contour_max - contour_min)
    contour_value = 0.5 * (contour_max + contour_min)
    contour.SetInputArrayToProcess(0, 0, 0, array.get("type"), array.get("text"))
    contour.SetValue(0, contour_value)

    # Update UI
    state.contour_min = contour_min
    state.contour_max = contour_max
    state.contour_value = contour_value
    state.contour_step = contour_step

    # Update View
    ctrl.view_update()


@state.change("contour_value")
def update_contour_value(contour_value, **kwargs):
    contour.SetValue(0, float(contour_value))
    ctrl.view_update()


# -----------------------------------------------------------------------------
# GUI elements
# -----------------------------------------------------------------------------


def standard_buttons():
    vuetify.VCheckbox(
        v_model=("cube_axes_visibility", True),
        on_icon="mdi-cube-outline",
        off_icon="mdi-cube-off-outline",
        classes="mx-1",
        hide_details=True,
        dense=True,
    )
    vuetify.VCheckbox(
        v_model="$vuetify.theme.dark",
        on_icon="mdi-lightbulb-off-outline",
        off_icon="mdi-lightbulb-outline",
        classes="mx-1",
        hide_details=True,
        dense=True,
    )
    vuetify.VCheckbox(
        v_model=("viewMode", "local"),
        on_icon="mdi-lan-disconnect",
        off_icon="mdi-lan-connect",
        true_value="local",
        false_value="remote",
        classes="mx-1",
        hide_details=True,
        dense=True,
    )
    with vuetify.VBtn(icon=True, click="$refs.view.resetCamera()"):
        vuetify.VIcon("mdi-crop-free")


def pipeline_widget():
    return VTreeview(
        sources=(
            "pipeline",
            [
                {"id": "1", "parent": "0", "visible": 1, "name": "Mesh"},
                {"id": "2", "parent": "1", "visible": 1, "name": "Contour"},
            ],
        ),
        actives_change=(actives_change, "[$event]"),
        visibility_change=(visibility_change, "[$event]"),
    )


def ui_card(title, ui_name):
    with vuetify.VCard(v_show=f"active_ui == '{ui_name}'"):
        vuetify.VCardTitle(
            title,
            classes="grey lighten-1 py-1 grey--text text--darken-3",
            style="user-select: none; cursor: pointer",
            hide_details=True,
            dense=True,
        )
        content = vuetify.VCardText(classes="py-2")
    return content


def mesh_card():
    with ui_card(title="Mesh", ui_name="mesh"):
        vuetify.VSelect(
            # Representation
            v_model=("mesh_representation", Representation.Surface),
            items=(
                "representations",
                [
                    {"text": "Points", "value": 0},
                    {"text": "Wireframe", "value": 1},
                    {"text": "Surface", "value": 2},
                    {"text": "SurfaceWithEdges", "value": 3},
                ],
            ),
            label="Representation",
            hide_details=True,
            dense=True,
            outlined=True,
            classes="pt-1",
        )
        with vuetify.VRow(classes="pt-2", dense=True):
            with vuetify.VCol(cols="6"):
                vuetify.VSelect(
                    # Color By
                    label="Color by",
                    v_model=("mesh_color_array_idx", 0),
                    items=("array_list", dataset_array),
                    hide_details=True,
                    dense=True,
                    outlined=True,
                    classes="pt-1",
                )
            with vuetify.VCol(cols="6"):
                vuetify.VSelect(
                    # Color Map
                    label="Colormap",
                    v_model=("mesh_color_preset", LookupTable.Rainbow),
                    items=(
                        "colormaps",
                        [
                            {"text": "Rainbow", "value": 0},
                            {"text": "Inv Rainbow", "value": 1},
                            {"text": "Greyscale", "value": 2},
                            {"text": "Inv Greyscale", "value": 3},
                        ],
                    ),
                    hide_details=True,
                    dense=True,
                    outlined=True,
                    classes="pt-1",
                )
        vuetify.VSlider(
            # Opacity
            v_model=("mesh_opacity", 1.0),
            min=0,
            max=1,
            step=0.1,
            label="Opacity",
            classes="mt-1",
            hide_details=True,
            dense=True,
        )


def contour_card():
    with ui_card(title="Contour", ui_name="contour"):
        vuetify.VSelect(
            # Contour By
            label="Contour by",
            v_model=("contour_by_array_idx", 0),
            items=("array_list", dataset_array),
            hide_details=True,
            dense=True,
            outlined=True,
            classes="pt-1",
        )
        vuetify.VSlider(
            # Contour Value
            v_model=("contour_value", contour_value),
            min=("contour_min", default_min),
            max=("contour_max", default_max),
            step=("contour_step", 0.01 * (default_max - default_min)),
            label="Value",
            classes="my-1",
            hide_details=True,
            dense=True,
        )
        vuetify.VSelect(
            # Representation
            v_model=("contour_representation", Representation.Surface),
            items=(
                "representations",
                [
                    {"text": "Points", "value": 0},
                    {"text": "Wireframe", "value": 1},
                    {"text": "Surface", "value": 2},
                    {"text": "SurfaceWithEdges", "value": 3},
                ],
            ),
            label="Representation",
            hide_details=True,
            dense=True,
            outlined=True,
            classes="pt-1",
        )
        with vuetify.VRow(classes="pt-2", dense=True):
            with vuetify.VCol(cols="6"):
                vuetify.VSelect(
                    # Color By
                    label="Color by",
                    v_model=("contour_color_array_idx", 0),
                    items=("array_list", dataset_array),
                    hide_details=True,
                    dense=True,
                    outlined=True,
                    classes="pt-1",
                )
            with vuetify.VCol(cols="6"):
                vuetify.VSelect(
                    # Color Map
                    label="Colormap",
                    v_model=("contour_color_preset", LookupTable.Rainbow),
                    items=(
                        "colormaps",
                        [
                            {"text": "Rainbow", "value": 0},
                            {"text": "Inv Rainbow", "value": 1},
                            {"text": "Greyscale", "value": 2},
                            {"text": "Inv Greyscale", "value": 3},
                        ],
                    ),
                    hide_details=True,
                    dense=True,
                    outlined=True,
                    classes="pt-1",
                )
        vuetify.VSlider(
            # Opacity
            v_model=("contour_opacity", 1.0),
            min=0,
            max=1,
            step=0.1,
            label="Opacity",
            classes="mt-1",
            hide_details=True,
            dense=True,
        )


# -----------------------------------------------------------------------------
# GUI
# -----------------------------------------------------------------------------

with SinglePageWithDrawerLayout(server) as layout:
    layout.title.set_text("CFD visualization")

    with layout.toolbar:
        # toolbar components
        vuetify.VSpacer()
        vuetify.VDivider(vertical=True, classes="mx-2")
        standard_buttons()

    with layout.drawer as drawer:
        # drawer components
        drawer.width = 325
        pipeline_widget()
        vuetify.VDivider(classes="mb-2")
        mesh_card()
        contour_card()

    with layout.content:
        # content components
        with vuetify.VContainer(
            fluid=True,
            classes="pa-0 fill-height",
        ):
            # view = vtk.VtkRemoteView(renderWindow, interactive_ratio=1)
            # view = vtk.VtkLocalView(renderWindow)
            view = vtk.VtkRemoteLocalView(
                renderWindow, namespace="view", mode="local", interactive_ratio=1
            )
            ctrl.view_update = view.update
            ctrl.view_reset_camera = view.reset_camera

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    server.start()


