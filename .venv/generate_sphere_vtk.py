import vtk

# Create a sphere source
sphere_source = vtk.vtkSphereSource()
sphere_source.SetCenter(0.0, 0.0, 0.0)
sphere_source.SetRadius(5.0)
sphere_source.SetThetaResolution(32)
sphere_source.SetPhiResolution(32)
sphere_source.Update()

# Write the sphere to a .vtk file
writer = vtk.vtkPolyDataWriter()
writer.SetFileName("sphere.vtk")
writer.SetInputData(sphere_source.GetOutput())
writer.Write()
