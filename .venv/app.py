from trame.app import get_server
from trame.ui.vuetify import SinglePageLayout
from trame.widgets import vtk as vtk_widget, vuetify
import vtkmodules.all as vtk
import os
import csv

# --- CONFIG --- #
file_path = "100um.csv"
use_csv = file_path.endswith(".csv")

# --- Load CSV into vtkPolyData --- #
def csv_to_polydata(csv_file):
    points = vtk.vtkPoints()
    temp_array = vtk.vtkFloatArray()
    temp_array.SetName("Temperature")

    with open(csv_file, newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            x = float(row["Particle X-Coordinate X Particle ID (Study 01 - Particles) [m]"]) * 100000
            y = float(row["Particle Y-Coordinate X Particle ID (Study 01 - Particles) [m]"]) * 100000
            z = float(row["Particle Z-Coordinate X Particle ID (Study 01 - Particles) [m]"]) * 100000
            temp = float(row["Temperature X Particle ID (Study 01 - Particles) [degC]"])
            points.InsertNextPoint(x, y, z)
            temp_array.InsertNextValue(temp)

    polydata = vtk.vtkPolyData()
    polydata.SetPoints(points)
    polydata.GetPointData().AddArray(temp_array)
    polydata.GetPointData().SetActiveScalars("Temperature")
    return polydata

# --- Load dataset --- #
if use_csv:
    polydata = csv_to_polydata(file_path)
else:
    reader = vtk.vtkDataSetReader()
    reader.SetFileName(file_path)
    reader.Update()
    polydata = reader.GetOutput()

# Convert to drawable points
glyph_filter = vtk.vtkVertexGlyphFilter()
glyph_filter.SetInputData(polydata)
glyph_filter.Update()

# Mapper
mapper = vtk.vtkPolyDataMapper()
mapper.SetInputConnection(glyph_filter.GetOutputPort())
mapper.SetScalarModeToUsePointData()
mapper.SetColorModeToMapScalars()
mapper.ScalarVisibilityOn()
mapper.SetScalarRange(polydata.GetPointData().GetScalars().GetRange())

# Actor
actor = vtk.vtkActor()
actor.SetMapper(mapper)
actor.GetProperty().SetPointSize(6)

# Cylinder "tank"
tank = vtk.vtkCylinderSource()
tank.SetRadius(8000)
tank.SetHeight(9000)
tank.SetResolution(100)
tank.CappingOff()

transform = vtk.vtkTransform()
transform.Translate(0, 4500, 0)

transform_filter = vtk.vtkTransformPolyDataFilter()
transform_filter.SetInputConnection(tank.GetOutputPort())
transform_filter.SetTransform(transform)
transform_filter.Update()

tank_mapper = vtk.vtkPolyDataMapper()
tank_mapper.SetInputConnection(transform_filter.GetOutputPort())

tank_actor = vtk.vtkActor()
tank_actor.SetMapper(tank_mapper)
tank_actor.GetProperty().SetColor(0.7, 0.7, 0.7)
tank_actor.GetProperty().SetOpacity(0.2)

# --- VTK Rendering Setup --- #
renderer = vtk.vtkRenderer()
renderer.AddActor(actor)
renderer.AddActor(tank_actor)
renderer.SetBackground(1, 1, 1)
renderer.ResetCamera()

render_window = vtk.vtkRenderWindow()
render_window.AddRenderer(renderer)

# Interactor required for RemoteView to work
interactor = vtk.vtkRenderWindowInteractor()
interactor.SetRenderWindow(render_window)

# --- Trame Setup --- #
server = get_server(client_type="vue2")
state, ctrl = server.state, server.controller

with SinglePageLayout(server) as layout:
    layout.title = "CFD Viewer with Animation (RemoteView)"
    with layout.content:
        with vuetify.VContainer():
            vuetify.VBtn("Toggle Rotation", click=ctrl.toggle_animation)
        vtk_widget.VtkRemoteView(render_window, ref="view")  # ✅ REAL-TIME VIEW

# --- Animation Logic --- #
def rotate():
    camera = renderer.GetActiveCamera()
    camera.Azimuth(1)
    render_window.Render()
    ctrl.view_update("view")  # ✅ update RemoteView

animation_flag = {"running": False}
timer = {"id": None}

@ctrl.add("toggle_animation")
def toggle_animation():
    if animation_flag["running"]:
        ctrl.remove_interval(timer["id"])
        animation_flag["running"] = False
    else:
        timer["id"] = ctrl.add_interval(30, rotate)
        animation_flag["running"] = True

# --- Start Server --- #
if __name__ == "__main__":
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
    server.start()
