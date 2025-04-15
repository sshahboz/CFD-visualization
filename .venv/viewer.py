from trame.app import get_server
from trame.ui.vuetify import SinglePageLayout
from trame.widgets import vtk as vtk_widget, vuetify
import vtkmodules.all as vtk
import random

# --- Globals for animation --- #
positions = []
velocities = []

# --- Create fake particles --- #
points = vtk.vtkPoints()
temps = vtk.vtkFloatArray()
temps.SetName("Temperature")

for i in range(1000):
    x, y, z = random.uniform(-100, 100), random.uniform(-100, 100), random.uniform(-100, 100)
    vx, vy, vz = random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)
    positions.append([x, y, z])
    velocities.append([vx, vy, vz])
    points.InsertNextPoint(x, y, z)
    temps.InsertNextValue(random.uniform(20, 100))

polydata = vtk.vtkPolyData()
polydata.SetPoints(points)
polydata.GetPointData().AddArray(temps)
polydata.GetPointData().SetActiveScalars("Temperature")

glyph_filter = vtk.vtkVertexGlyphFilter()
glyph_filter.SetInputData(polydata)
glyph_filter.Update()

mapper = vtk.vtkPolyDataMapper()
mapper.SetInputConnection(glyph_filter.GetOutputPort())
mapper.SetScalarRange(polydata.GetPointData().GetScalars().GetRange())

actor = vtk.vtkActor()
actor.SetMapper(mapper)
actor.GetProperty().SetPointSize(5)

renderer = vtk.vtkRenderer()
renderer.AddActor(actor)
renderer.SetBackground(1, 1, 1)
renderer.ResetCamera()

render_window = vtk.vtkRenderWindow()
render_window.AddRenderer(renderer)
render_window.Render()

interactor = vtk.vtkRenderWindowInteractor()
interactor.SetRenderWindow(render_window)
interactor.Initialize()

# --- Trame Setup --- #
server = get_server(client_type="vue2")
state, ctrl = server.state, server.controller

@ctrl.add("move_particles")
def move_particles():
    dt = 0.5  # Large step to make movement obvious
    for i in range(len(positions)):
        for j in range(3):
            positions[i][j] += velocities[i][j] * dt
        polydata.GetPoints().SetPoint(i, *positions[i])
    polydata.GetPoints().Modified()
    polydata.Modified()
    glyph_filter.Update()
    render_window.Render()
    print(f"Frame updated | Pos: {positions[0]}")

# --- Trame UI --- #
with SinglePageLayout(server) as layout:
    layout.title = "Local Particle Motion - Guaranteed Visible"
    with layout.content:
        with vuetify.VContainer():
            vuetify.VBtn("Start Motion", id="motion-btn")
        vtk_widget.VtkLocalView(render_window)

        from trame.widgets.html import Div
        Div(
            """
            <script>
                let moving = false;
                let timer;
                function toggleMotion() {
                    if (!moving) {
                        moving = true;
                        timer = setInterval(() => trame.trigger("move_particles"), 50);
                    } else {
                        clearInterval(timer);
                        moving = false;
                    }
                }
                document.addEventListener("DOMContentLoaded", function () {
                    document.getElementById("motion-btn").addEventListener("click", toggleMotion);
                });
            </script>
            """,
            style="display:none;"
        )

# --- Run --- #
if __name__ == "__main__":
    server.start()
