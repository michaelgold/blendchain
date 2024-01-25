from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Tuple, Optional
import bpy
import os
from datetime import datetime
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import math


app = FastAPI()
image_url = ""

# Directory for rendered images
rendered_images_dir = "rendered_images"
os.makedirs(rendered_images_dir, exist_ok=True)

# Directory for rendered images
rendered_images_dir = "rendered_images"
os.makedirs(rendered_images_dir, exist_ok=True)

# Mount the static directory to serve rendered images
app.mount("/static", StaticFiles(directory=rendered_images_dir), name="static")


# Pydantic models
class Vector3D(BaseModel):
    x: float
    y: float
    z: float


class ObjectTransform(BaseModel):
    location: Vector3D = None
    rotation: Vector3D = None
    scale: Vector3D = None


class BlenderObject(BaseModel):
    name: str
    type: str
    object_transform: ObjectTransform


class SceneGraph(BaseModel):
    objects: List[BlenderObject]


class OperationResult(BaseModel):
    message: str
    scene_graph: SceneGraph


class RenderedScene(BaseModel):
    rendered_image_url: str
    scene_graph: SceneGraph


# def deg2rad(deg):
#     return deg * math.pi / 180


# def rad2deg(rad):
#     return rad * 180 / math.pi


def get_scene_graph() -> SceneGraph:
    objects = []
    for obj in bpy.data.objects:
        rotation_euler = (
            obj.rotation_euler
            if obj.rotation_mode == "XYZ"
            else obj.rotation_quaternion.to_euler("XYZ")
        )

        location = Vector3D(x=obj.location.x, y=obj.location.y, z=obj.location.z)
        rotation = Vector3D(
            x=math.degrees(rotation_euler.x),
            y=math.degrees(rotation_euler.y),
            z=math.degrees(rotation_euler.z),
        )
        scale = Vector3D(x=obj.scale.x, y=obj.scale.y, z=obj.scale.z)

        blender_object = BlenderObject(
            name=obj.name,
            type=obj.type,
            object_transform=ObjectTransform(
                location=location, rotation=rotation, scale=scale
            ),
        )
        objects.append(blender_object)

    return SceneGraph(objects=objects)


def get_rendered_scene(rendered_image_url: str) -> RenderedScene:
    scene_graph = get_scene_graph()

    return RenderedScene(rendered_image_url=rendered_image_url, scene_graph=scene_graph)


@app.get("/scene_graph", response_model=SceneGraph)
async def scene_graph():
    global image_url
    # Render settings and process

    return get_scene_graph()


@app.post("/render_scene", response_model=RenderedScene)
async def render_scene():
    global image_url
    # Render settings and process
    filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"
    filepath = os.path.join(rendered_images_dir, filename)
    bpy.context.scene.render.filepath = filepath
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)

    # URL to access the rendered image
    image_url = f"http://127.0.0.1:8000/static/{filename}"

    # Get the rendered scene
    rendered_scene = get_rendered_scene(image_url)
    return rendered_scene


@app.post("/add_cube", response_model=OperationResult)
async def add_cube():
    bpy.ops.mesh.primitive_cube_add()
    operation_result = OperationResult(
        message="Cube added", scene_graph=get_scene_graph()
    )
    return operation_result


@app.post("/add_sphere", response_model=OperationResult)
async def add_sphere():
    bpy.ops.mesh.primitive_uv_sphere_add()
    operation_result = OperationResult(
        message="Sphere added", scene_graph=get_scene_graph()
    )
    return operation_result


@app.post("/add_torus", response_model=OperationResult)
async def add_torus():
    bpy.ops.mesh.primitive_torus_add()
    operation_result = OperationResult(
        message="Torus added", scene_graph=get_scene_graph()
    )
    return operation_result


@app.post("/add_cylinder", response_model=OperationResult)
async def add_cylinder():
    bpy.ops.mesh.primitive_cylinder_add()
    operation_result = OperationResult(
        message="Cylinder added", scene_graph=get_scene_graph()
    )


def get_object(name: str):
    obj = [obj for obj in bpy.data.objects if obj.name.lower() == name.lower()]
    return obj[0] if obj else None


@app.post("/transform_object", response_model=OperationResult)
async def transform_object(name: str, transform_input: ObjectTransform):
    obj = get_object(name)
    if not obj:
        return OperationResult(
            message=f"Object {name} not found", scene_graph=get_scene_graph()
        )

    if transform_input.location:
        obj.location = (
            transform_input.location.x,
            transform_input.location.y,
            transform_input.location.z,
        )
    if transform_input.rotation:
        obj.rotation_euler = (
            math.radians(transform_input.rotation.x),
            math.radians(transform_input.rotation.y),
            math.radians(transform_input.rotation.z),
        )
    if transform_input.scale:
        obj.scale = (
            transform_input.scale.x,
            transform_input.scale.y,
            transform_input.scale.z,
        )
    obj.update_tag()  # Update the object to see the changes
    bpy.context.view_layer.update()  # Update the scene

    # save blendet file
    download_path = Path(Path.home() / "Downloads")
    filepath = str(download_path / "test.blend")
    bpy.ops.wm.save_mainfile(filepath=filepath)
    print(f"Saved file to {filepath}")

    operation_result = OperationResult(
        message=f"Object {name} transformed", scene_graph=get_scene_graph()
    )
    return operation_result


@app.post("/delete_object", response_model=OperationResult)
async def delete_object(name: str) -> SceneGraph:
    obj = bpy.data.objects.get(name)
    if obj:
        bpy.data.objects.remove(obj)
        operation_result = OperationResult(
            message=f"Object {name} deleted", scene_graph=get_scene_graph()
        )
        return operation_result
    else:
        operation_result = OperationResult(
            message=f"Object {name} not found", scene_graph=get_scene_graph()
        )
        return operation_result


# Run the server
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
