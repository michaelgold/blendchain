from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List, Tuple, Optional
import bpy
import os
from datetime import datetime
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)


import math


app = FastAPI()
image_url = ""


# @app.post("/api_interaction")
# async def api_interaction(request: Request):
#     global openapi_agent
#     if not openapi_agent:
#         ollama_model = OllamaModel(api_key='your_api_key')
#         openapi_agent = create_openapi_agent(ollama_model, openapi_toolkit)
#     body = await request.json()
#     user_query = body.get("query")
#     response = openapi_agent.run(user_query)
#     return response

# Create the OpenAPI agent


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
    id: str = None
    name: str
    type: str
    object_transform: ObjectTransform

    # default id = name
    def __init__(self, **data):
        super().__init__(**data)
        if not self.id:
            self.id = self.name


class SceneGraph(BaseModel):
    objects: List[BlenderObject]


class OperationResult(BaseModel):
    message: str
    active_object: BlenderObject = None
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


# def get_object(name: str):


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
        message="Cube added",
        active_object=get_active_object(),
        scene_graph=get_scene_graph(),
    )
    return operation_result


@app.post("/add_sphere", response_model=OperationResult)
async def add_sphere():
    bpy.ops.mesh.primitive_uv_sphere_add()
    operation_result = OperationResult(
        message="Sphere added",
        active_object=get_active_object(),
        scene_graph=get_scene_graph(),
    )
    return operation_result


def get_blender_object(obj_name: str) -> BlenderObject:
    scene_graph = get_scene_graph()
    obj = [obj for obj in scene_graph.objects if obj.name.lower() == obj_name.lower()][
        0
    ]
    blender_object = BlenderObject(
        name=obj.name,
        type=obj.type,
        object_transform=ObjectTransform(
            location=obj.object_transform.location,
            rotation=obj.object_transform.rotation,
            scale=obj.object_transform.scale,
        ),
    )
    return blender_object


def get_active_object() -> BlenderObject | None:
    obj_name = bpy.context.view_layer.objects.active.name
    if not obj_name:
        return None
    else:
        return get_blender_object(obj_name)


@app.post("/add_torus", response_model=OperationResult)
async def add_torus():
    bpy.ops.mesh.primitive_torus_add()
    logging.log(
        logging.INFO,
        f"Torus added\nActive object: {bpy.context.view_layer.objects.active.name}",
    )

    operation_result = OperationResult(
        message="Torus added",
        active_object=get_active_object(),
        scene_graph=get_scene_graph(),
    )
    return operation_result


@app.post("/add_cylinder", response_model=OperationResult)
async def add_cylinder():
    bpy.ops.mesh.primitive_cylinder_add()
    operation_result = OperationResult(
        message="Cylinder added",
        active_object=get_active_object(),
        scene_graph=get_scene_graph(),
    )
    return operation_result


def get_object(name: str) -> bpy.types.Object | None:
    obj = [obj for obj in bpy.data.objects if obj.name.lower() == name.lower()]
    return obj[0] if obj else None


@app.post("/set_object_transformation", response_model=OperationResult)
async def set_object_transformation(name: str, transform_input: ObjectTransform):
    """Set object's location, rotation, and scale"""
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
        message=f"Object {name} transformed",
        active_object=get_active_object(),
        scene_graph=get_scene_graph(),
    )
    return operation_result


@app.post("/rotate_object", response_model=OperationResult)
async def rotate_object(name: str, rotation_input: Vector3D):
    """Rotate object by x, y, z degrees"""
    obj = get_object(name)
    if not obj:
        return OperationResult(
            message=f"Object {name} not found", scene_graph=get_scene_graph()
        )
    blender_object = get_blender_object(name)

    updated_x = blender_object.object_transform.rotation.x + rotation_input.x
    updated_y = blender_object.object_transform.rotation.y + rotation_input.y
    updated_z = blender_object.object_transform.rotation.z + rotation_input.z

    if rotation_input:
        obj.rotation_euler = (
            math.radians(updated_x),
            math.radians(updated_y),
            math.radians(updated_z),
        )

    obj.update_tag()  # Update the object to see the changes
    bpy.context.view_layer.update()  # Update the scene

    operation_result = OperationResult(
        message=f"Object {name} transformed",
        active_object=get_active_object(),
        scene_graph=get_scene_graph(),
    )
    return operation_result


@app.post("/move_object", response_model=OperationResult)
async def move_object(name: str, location_input: Vector3D):
    """Move object by x, y, z"""
    obj = get_object(name)
    if not obj:
        return OperationResult(
            message=f"Object {name} not found", scene_graph=get_scene_graph()
        )
    blender_object = get_blender_object(name)

    updated_x = blender_object.object_transform.location.x + location_input.x
    updated_y = blender_object.object_transform.location.y + location_input.y
    updated_z = blender_object.object_transform.location.z + location_input.z

    if location_input:
        obj.location = (
            updated_x,
            updated_y,
            updated_z,
        )

    obj.update_tag()  # Update the object to see the changes
    bpy.context.view_layer.update()  # Update the scene

    operation_result = OperationResult(
        message=f"Object {name} transformed",
        active_object=get_active_object(),
        scene_graph=get_scene_graph(),
    )
    return operation_result


@app.post("/scale_object", response_model=OperationResult)
async def scale_object(name: str, scale_input: Vector3D):
    """Scale object by x, y, z"""
    obj = get_object(name)
    if not obj:
        return OperationResult(
            message=f"Object {name} not found", scene_graph=get_scene_graph()
        )
    blender_object = get_blender_object(name)

    updated_x = blender_object.object_transform.scale.x * scale_input.x
    updated_y = blender_object.object_transform.scale.y * scale_input.y
    updated_z = blender_object.object_transform.scale.z * scale_input.z

    if scale_input:
        obj.scale = (
            updated_x,
            updated_y,
            updated_z,
        )

    obj.update_tag()  # Update the object to see the changes
    bpy.context.view_layer.update()  # Update the scene

    operation_result = OperationResult(
        message=f"Object {name} transformed",
        active_object=get_active_object(),
        scene_graph=get_scene_graph(),
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
