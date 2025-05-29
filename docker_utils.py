import docker
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# --- Docker Client Initialization ---

def get_docker_client(docker_host=None):
    """Initializes and returns a Docker client.

    Args:
        docker_host (str, optional): The URL or path to the Docker daemon socket.
                                     Defaults to None, which uses docker.from_env().

    Returns:
        docker.DockerClient: An initialized Docker client instance.
        None: If connection to Docker daemon fails.
    """
    try:
        if docker_host:
            client = docker.DockerClient(base_url=docker_host)
        else:
            # Connect using environment settings (e.g., DOCKER_HOST or default socket)
            client = docker.from_env()
        # Test the connection
        client.ping()
        log.info("Successfully connected to Docker daemon.")
        return client
    except docker.errors.DockerException as e:
        log.error(f"Failed to connect to Docker daemon: {e}")
        return None
    except Exception as e:
        log.error(f"An unexpected error occurred while connecting to Docker: {e}")
        return None

# --- Container Management Functions ---

def start_challenge_container(client, image_name, user_id, challenge_id, ports_config=None, env_vars=None, cpu_limit=None, mem_limit=None):
    """Starts a new Docker container for a specific challenge and user.

    Args:
        client (docker.DockerClient): The Docker client instance.
        image_name (str): The name of the Docker image to use.
        user_id (int): The ID of the user starting the challenge.
        challenge_id (int): The ID of the challenge.
        ports_config (dict, optional): Dictionary for port mapping (e.g., {'80/tcp': 8080}). Defaults to None.
        env_vars (dict, optional): Dictionary of environment variables. Defaults to None.
        cpu_limit (str, optional): CPU limit (e.g., '1'). Defaults to None.
        mem_limit (str, optional): Memory limit (e.g., '512m'). Defaults to None.

    Returns:
        docker.models.containers.Container: The started container object.
        None: If container startup fails.
    """
    container_name = f"ctfd-{user_id}-{challenge_id}" # Basic naming convention
    try:
        log.info(f"Attempting to start container '{container_name}' from image '{image_name}'...")

        # Check if container already exists (optional, depends on desired behavior)
        try:
            existing_container = client.containers.get(container_name)
            log.warning(f"Container '{container_name}' already exists. Reusing or error handling needed? Stopping for now.")
            # Decide policy: reuse, error, or remove and recreate. For now, remove.
            existing_container.stop()
            existing_container.remove()
        except docker.errors.NotFound:
            pass # Container doesn't exist, proceed

        # Pull image if not present
        try:
            client.images.get(image_name)
        except docker.errors.ImageNotFound:
            log.info(f"Image '{image_name}' not found locally. Pulling...")
            client.images.pull(image_name)
            log.info(f"Image '{image_name}' pulled successfully.")

        # Prepare container configuration
        container_params = {
            "image": image_name,
            "name": container_name,
            "detach": True,
            "ports": ports_config, # e.g., {'container_port/tcp': host_port}
            "environment": env_vars,
            "labels": {
                "ctfd_managed": "true",
                "user_id": str(user_id),
                "challenge_id": str(challenge_id)
            }
            # Add resource limits if specified
            # Note: Exact parameter names might vary slightly based on Docker SDK version
            # "cpu_shares": ..., "mem_limit": ... need careful mapping
        }

        # Add resource limits (adjust parameter names as needed for your Docker SDK version)
        # Example using common parameters, verify with SDK docs
        nano_cpus = int(float(cpu_limit) * 1e9) if cpu_limit else None
        if nano_cpus:
             container_params['nano_cpus'] = nano_cpus
        if mem_limit:
             container_params['mem_limit'] = mem_limit

        container = client.containers.run(**container_params)
        log.info(f"Container '{container.name}' (ID: {container.short_id}) started successfully.")
        return container

    except docker.errors.ImageNotFound:
        log.error(f"Image '{image_name}' not found and could not be pulled.")
        return None
    except docker.errors.APIError as e:
        log.error(f"Docker API error while starting container '{container_name}': {e}")
        return None
    except Exception as e:
        log.error(f"An unexpected error occurred while starting container '{container_name}': {e}")
        return None

def stop_container(client, container_id):
    """Stops and removes a Docker container.

    Args:
        client (docker.DockerClient): The Docker client instance.
        container_id (str): The ID or name of the container to stop.

    Returns:
        bool: True if stopped and removed successfully, False otherwise.
    """
    try:
        container = client.containers.get(container_id)
        log.info(f"Stopping container '{container.name}' (ID: {container.short_id})...")
        container.stop()
        log.info(f"Removing container '{container.name}' (ID: {container.short_id})...")
        container.remove()
        log.info(f"Container '{container.name}' stopped and removed successfully.")
        return True
    except docker.errors.NotFound:
        log.warning(f"Container '{container_id}' not found. Cannot stop or remove.")
        return False
    except docker.errors.APIError as e:
        log.error(f"Docker API error while stopping/removing container '{container_id}': {e}")
        return False
    except Exception as e:
        log.error(f"An unexpected error occurred while stopping/removing container '{container_id}': {e}")
        return False

def get_container_details(client, container_id):
    """Gets details about a specific container.

    Args:
        client (docker.DockerClient): The Docker client instance.
        container_id (str): The ID or name of the container.

    Returns:
        dict: A dictionary containing container attributes.
        None: If the container is not found or an error occurs.
    """
    try:
        container = client.containers.get(container_id)
        return container.attrs
    except docker.errors.NotFound:
        log.warning(f"Container '{container_id}' not found.")
        return None
    except docker.errors.APIError as e:
        log.error(f"Docker API error while getting details for container '{container_id}': {e}")
        return None
    except Exception as e:
        log.error(f"An unexpected error occurred while getting details for container '{container_id}': {e}")
        return None

def list_managed_containers(client, user_id=None, challenge_id=None):
    """Lists containers managed by this plugin, optionally filtered.

    Args:
        client (docker.DockerClient): The Docker client instance.
        user_id (int, optional): Filter by user ID. Defaults to None.
        challenge_id (int, optional): Filter by challenge ID. Defaults to None.

    Returns:
        list: A list of container objects managed by the plugin.
    """
    filters = {"label": "ctfd_managed=true"}
    if user_id:
        filters["label"] = f"user_id={user_id}"
    if challenge_id:
        filters["label"] = f"challenge_id={challenge_id}"
    # Combine filters if both are provided
    if user_id and challenge_id:
         filters["label"] = [f"ctfd_managed=true", f"user_id={user_id}", f"challenge_id={challenge_id}"]

    try:
        managed_containers = client.containers.list(all=True, filters=filters)
        return managed_containers
    except docker.errors.APIError as e:
        log.error(f"Docker API error while listing managed containers: {e}")
        return []
    except Exception as e:
        log.error(f"An unexpected error occurred while listing managed containers: {e}")
        return []

# --- Helper Functions ---

def get_container_ip_port(container_attrs, container_port):
    """Extracts the host IP and port for a specific container port.

    Args:
        container_attrs (dict): The container attributes dictionary (from container.attrs).
        container_port (str): The container port string (e.g., '80/tcp').

    Returns:
        tuple: (host_ip, host_port) or (None, None) if not found.
    """
    try:
        ports = container_attrs.get('NetworkSettings', {}).get('Ports', {})
        if container_port in ports and ports[container_port] is not None:
            # Typically returns a list of mappings, take the first one
            mapping = ports[container_port][0]
            host_ip = mapping.get('HostIp', '0.0.0.0') # Default to 0.0.0.0 if not specified
            host_port = mapping.get('HostPort')
            return host_ip, host_port
    except (KeyError, IndexError, TypeError) as e:
        log.error(f"Error parsing port information for {container_port}: {e}")
    return None, None

