from trame.app import get_server
from trame.ui.vuetify import SinglePageLayout
from trame.widgets import vtk as vtk_widget
import vtkmodules.all as vtk
import os

# Path
vtk_file_path = "samplevtk/cylinder.vtk"  # Replace with your file name

reader = vtk.vtkDataSetReader()
reader.SetFileName(vtk_file_path)
reader.Update()

mapper = vtk.vtkDataSetMapper()
mapper.SetInputConnection(reader.GetOutputPort())

actor = vtk.vtkActor()
actor.SetMapper(mapper)

# Renderer
renderer = vtk.vtkRenderer()
renderer.AddActor(actor)
renderer.SetBackground(0.1, 0.1, 0.1)
renderer.ResetCamera()

renderWindow = vtk.vtkRenderWindow()
renderWindow.AddRenderer(renderer)

# Trame App
server = get_server(client_type="vue2")
state, ctrl = server.state, server.controller

with SinglePageLayout(server) as layout:
    layout.title = "CFD Visualizer - VTK Simulation"

    with layout.content:
        vtk_widget.VtkLocalView(renderWindow)

if __name__ == "__main__":
    if not os.path.exists(vtk_file_path):
        print(f"File not found: {vtk_file_path}")
    server.start()
