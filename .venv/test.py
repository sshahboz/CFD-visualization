from trame.app import get_server
from trame.ui.vuetify import SinglePageLayout
from trame.widgets import vtk
import vtkmodules.all as vtkModules

# Create VTK rendering pipeline
cube = vtkModules.vtkCubeSource()

mapper = vtkModules.vtkPolyDataMapper()
mapper.SetInputConnection(cube.GetOutputPort())

actor = vtkModules.vtkActor()
actor.SetMapper(mapper)

renderer = vtkModules.vtkRenderer()
renderer.AddActor(actor)
renderer.ResetCamera()

renderWindow = vtkModules.vtkRenderWindow()
renderWindow.AddRenderer(renderer)

# Get Trame server and configure layout
server = get_server(client_type="vue2")
state, ctrl = server.state, server.controller

with SinglePageLayout(server) as layout:
    layout.title = "CFD Cube Viewer"

    with layout.content:
        vtk.VtkLocalView(renderWindow)

if __name__ == "__main__":
    server.start()
