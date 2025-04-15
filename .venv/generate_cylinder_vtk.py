import vtkmodules.all as vtk

# Create a cylinder
cylinder = vtk.vtkCylinderSource()
cylinder.SetRadius(0.5)
cylinder.SetHeight(1.0)
cylinder.SetResolution(50)
cylinder.Update()

# Write the output to a legacy .vtk file (PolyData format)
writer = vtk.vtkPolyDataWriter()
writer.SetFileName("cylinder.vtk")
writer.SetInputData(cylinder.GetOutput())
writer.Write()

print("Cylinder saved to 'cylinder.vtk'")
