# BlendChain Project

BlendChain leverages the power of ollama, langchain, FastAPI endpoints.


## Features
**Language Server:** A FastAPI-based language server offering a wide range of processing capabilities.

**Custom Planning:** Tailor-made planning solutions to address specific use cases.

**Extensibility:** Designed for easy integration and extension with other services or modules.

## Requirements
Python 3.10.10 (for Blender compatibility)

## Installation

Clone the repository and install the dependencies:

``` bash
git clone https://github.com/michaelgold/blendchain.git
cd blendchain
pip install -r requirements.txt
```

Install the custom build of Blender's Python module with code hints with this command:

``` bash
pip install --index-url https://michaelgold.github.io/buildbpy bpy=4.0.2
```


## Dependencies
**bpy:** For 3D modeling operations.

**Cython, numpy:** For high-performance computing operations.

**pydantic, requests:** For data validation and making HTTP requests.

**zstandard:** For compression tasks.
**ollama, langchain:** For advanced language processing.
Usage
The project consists of multiple components, each designed to run as a separate service:

## Starting the Language Server
Run the following command to start the language server on port 8001:

```bash
uvicorn langserver:app --reload 
--port 8001
```

Starting the Main Service
To start the main BlendChain service on port 8000:

``` bash
uvicorn main:app --reload --port 8000
```

`main.py:`
Static Files Mounting
/static: This endpoint serves static files from the rendered_images directory, allowing access to rendered images via a static URL.

### Pydantic Models
Several Pydantic models are defined to structure the data for requests and responses:

Vector3D: Represents a 3D vector with x, y, and z float components.
ObjectTransform: Holds transformation information (location, rotation, scale) for a Blender object, using Vector3D.
BlenderObject: Describes a Blender object with an optional ID, name, type, and its transformation.
SceneGraph: Represents a scene graph containing a list of BlenderObjects.
OperationResult: Used for responses, includes a message, the active Blender object, and the current scene graph.
RenderedScene: Contains the URL to a rendered image and the associated scene graph.

## Endpoints
The `main.py` file defines several endpoints for manipulating 3D objects within Blender. Each endpoint returns an `OperationResult` or a `RenderedScene` object, providing feedback on the operation's success, details of the active object, and the updated scene graph.


`/add_cube`, `/add_sphere`, `/add_torus`, `/add_cylinder`: These endpoints allow adding different types of objects (cube, sphere, torus, cylinder) to the Blender scene. They require specifying parameters for the object's placement and transformations.

`/set_object_transformation`: Sets the location, rotation, and scale of an object specified by its name.

`/rotate_object`: Rotates an object by specified degrees around the x, y, and z axes.

`/move_object`: Moves an object by specified amounts along the x, y, and z axes.

`/scale_object`: Scales an object by specified factors along the x, y, and z axes.

`/delete_object`: Deletes an object from the scene based on its name.
Each of these endpoints requires specific input parameters, typically including the name of the object to be manipulated and the desired transformation parameters (represented as Vector3D for location, rotation, and scale).

## Prompting the FastAPI Endpoints

http://localhost:8001/docs for the LangChain server. This will open the Swagger UI interface for each application.

### Using Swagger UI
The Swagger UI provides a user-friendly web interface to interact with all the API endpoints defined in your FastAPI application. Here’s how to use it:

#### Explore Endpoints: 
The `/docs` page lists all the available API endpoints, along with their HTTP methods (GET, POST, etc.), summaries, and descriptions. Click on any endpoint to expand its details.

#### Try Out Requests: 
For each endpoint, you can click the "Try it out" button, which allows you to fill in any required parameters or request bodies. After inputting the necessary information, click "Execute" to make a live API call.

#### View Responses:
Once you've executed a request, the interface will display the actual request made, the server's response code, the response body, and headers. This is useful for debugging and understanding how your API behaves with different inputs.

#### Working with Specific Endpoints:
The BlendChain project's `/docs` will display endpoints like `/scene_graph`, `/render_scene`, and object manipulation endpoints (`/add_cube`, `/add_sphere`, etc.), allowing you to interact with the scene graph and render scenes through the API.

The LangChain Server's `/docs` will offer endpoints related to API interaction schemas, config schemas, and invoking LangChain functionalities, providing a way to test and use LangChain's Runnable interfaces directly through the API.

To use the `/api_interaction/invoke` endpoint on your FastAPI server running at http://127.0.0.1:8001/docs, follow these steps to invoke the runnable with the given input and optionally, a configuration. This endpoint is designed for executing specific tasks or processes based on the input provided to the LangChain server's API.

- Step 1: Accessing Swagger UI
Open your web browser and navigate to http://127.0.0.1:8001/docs. This URL opens the Swagger UI for your FastAPI application, providing an interactive API documentation.
- Step 2: Locating the Endpoint
In the Swagger UI, scroll or search for the /api_interaction/invoke endpoint. You'll find it listed under the api_interaction tag. This endpoint is for invoking the runnable with specified input and configuration.
- Step 3: Trying Out the Endpoint
Click on the /api_interaction/invoke section to expand it, then click the "Try it out" button. This enables you to interactively use the endpoint right from the browser.
- Step 4: Configuring the Request
You will see input fields for the request body. The required structure for the request body typically includes:
input: This field requires you to specify the input to the runnable in the form of a JSON object. The structure of this input depends on the specific runnable you are targeting.
config (optional): This JSON object allows you to pass configuration parameters to the runnable. Although it's optional, providing it can customize the execution context.
kwargs (optional): This is for additional keyword arguments that you might need to pass to the runnable. It's typically a JSON object with key-value pairs.
- Step 5: Sending the Request
Fill in the input, config, and kwargs fields with the appropriate JSON data for your use case. Once you've configured the request to your needs, click the "Execute" button to send the request to the server.
- Step 6: Reviewing the Response
After execution, scroll down to see the server's response. The response section will display the status code, the response body, and any headers. If the invocation was successful, you should see a 200 status code along with the output of the runnable in the response body.

Example Request Body
Here's an example of a simple request body you might use with the /api_interaction/invoke endpoint:

``` json
{
  "input": {
    "input": {
      "text": "Add a cube to the scene"
    }
  },
  "config": {},
  "kwargs": {}
}

``` 


Refer to launch.json for more details on configuration options.

