"""Offscreen pyvista rendering of Kratos triangle meshes.

Every figure in ../data is produced by these helpers - nothing is
hand-drawn, so re-running the scripts regenerates the documentation.
"""

import numpy
import pyvista

pyvista.OFF_SCREEN = True


def PolyDataFromModelPart(model_part):
    """A pyvista surface carrying the current mesh (triangles only)."""
    node_ids = numpy.array([node.Id for node in model_part.Nodes], dtype=numpy.int64)
    row = {int(node_id): index for index, node_id in enumerate(node_ids)}
    points = numpy.array([[node.X, node.Y, node.Z] for node in model_part.Nodes])
    faces = []
    for element in model_part.Elements:
        triangle = [row[node.Id] for node in element.GetGeometry()]
        faces.append([3, *triangle])
    return pyvista.PolyData(points, numpy.asarray(faces, dtype=numpy.int64))


def RenderFields(model_part, fields, path, shape=None, clim_share=(), zoom=1.15,
                 window_size=(1500, 520)):
    """Renders named nodal arrays side by side into one PNG.

    Args:
        fields: list of (title, values, colormap) triples; values are
            per-node arrays aligned with model_part.Nodes order.
        clim_share: indices of panels forced onto a common color range, so
            e.g. solver vs surrogate panels are visually comparable.
    """
    surface = PolyDataFromModelPart(model_part)
    shape = shape or (1, len(fields))

    shared_limits = None
    if clim_share:
        values = numpy.concatenate([numpy.asarray(fields[i][1]).ravel() for i in clim_share])
        shared_limits = (float(values.min()), float(values.max()))

    plotter = pyvista.Plotter(shape=shape, off_screen=True, window_size=window_size,
                              border=False)
    plotter.set_background("white")
    for index, (title, values, colormap) in enumerate(fields):
        plotter.subplot(index // shape[1], index % shape[1])
        panel = surface.copy()
        # unique array/bar name per panel: pyvista shares scalar bars (and
        # their lookup tables) between panels with the same title
        name = f"[{index}] {title}"
        panel[name] = numpy.asarray(values).ravel()
        limits = shared_limits if index in clim_share else None
        plotter.add_mesh(panel, scalars=name, cmap=colormap, clim=limits,
                         show_edges=False,
                         scalar_bar_args={"title": name, "vertical": False,
                                          "position_x": 0.16, "position_y": 0.015,
                                          "width": 0.68, "height": 0.1,
                                          "title_font_size": 15,
                                          "label_font_size": 12, "color": "black",
                                          "fmt": "%.3g", "n_labels": 3})
        plotter.view_xy()
        plotter.camera.zoom(zoom)
    plotter.screenshot(str(path))
    plotter.close()
    return path
