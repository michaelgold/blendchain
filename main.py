from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Tuple
import bpy
import os
from datetime import datetime
from fastapi.staticfiles import StaticFiles


app = FastAPI()

# Directory for rendered images
rendered_images_dir = "rendered_images"
os.makedirs(rendered_images_dir, exist_ok=True)

# Directory for rendered images
rendered_images_dir = "rendered_images"
os.makedirs(rendered_images_dir, exist_ok=True)

# Mount the static directory to serve rendered images
app.mount("/static", StaticFiles(directory=rendered_images_dir), name="static")


# Pydantic models
class BlenderObject(BaseModel):
    name: str
    type: str
    location: Tuple[float, float, float]
    rotation: Tuple[float, float, float]
    scale: Tuple[float, float, float]


class SceneGraph(BaseModel):
    objects: List[BlenderObject]
    rendered_image_url: str


# Function to get the scene graph
def get_scene_graph(rendered_image_url: str) -> SceneGraph:
    objects = []
    for obj in bpy.data.objects:
        # Convert the rotation to Euler angles if it's not already
        rotation_euler = (
            obj.rotation_euler
            if obj.rotation_mode == "XYZ"
            else obj.rotation_quaternion.to_euler("XYZ")
        )

        # Create a BlenderObject instance
        blender_object = BlenderObject(
            name=obj.name,
            type=obj.type,
            location=tuple(obj.location),
            rotation=tuple(rotation_euler),
            scale=tuple(obj.scale),
        )
        objects.append(blender_object)

    return SceneGraph(objects=objects, rendered_image_url=rendered_image_url)


@app.post("/render_scene", response_model=SceneGraph)
async def render_scene():
    # Render settings and process
    filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"
    filepath = os.path.join(rendered_images_dir, filename)
    bpy.context.scene.render.filepath = filepath
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)

    # URL to access the rendered image
    image_url = f"http://127.0.0.1:8000/static/{filename}"

    # Get the scene graph
    scene_graph = get_scene_graph(rendered_image_url=image_url)
    return scene_graph


@app.post("/add_cube")
async def add_cube():
    bpy.ops.mesh.primitive_cube_add()
    return {"message": "Cube added"}


@app.post("/add_sphere")
async def add_sphere():
    bpy.ops.mesh.primitive_uv_sphere_add()
    return {"message": "Sphere added"}


@app.post("/add_torus")
async def add_torus():
    bpy.ops.mesh.primitive_torus_add()
    return {"message": "Torus added"}


@app.post("/add_cylinder")
async def add_cylinder():
    bpy.ops.mesh.primitive_cylinder_add()
    return {"message": "Cylinder added"}


@app.post("/transform_object")
async def transform_object(
    name: str, location: list = None, rotation: list = None, scale: list = None
):
    obj = bpy.data.objects.get(name)
    if not obj:
        return {"error": "Object not found"}

    if location:
        obj.location = location
    if rotation:
        obj.rotation_euler = rotation
    if scale:
        obj.scale = scale

    return {"message": f"Object {name} transformed"}


@app.post("/delete_object")
async def delete_object(name: str):
    obj = bpy.data.objects.get(name)
    if obj:
        bpy.data.objects.remove(obj)
        return {"message": f"Object {name} deleted"}
    else:
        return {"error": "Object not found"}


# Run the server
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
