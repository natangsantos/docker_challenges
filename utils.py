import docker
import os
import time

#client = docker.from_env()
client = docker.DockerClient(base_url='unix:///var/run/docker.sock')

container_map = {}  # In-memory structure: container_name -> {url, timestamp, id}

TIMEOUT_SECONDS = 1800  # 30 minutes

def launch_secure_container(challenge_id, user_id):
    container_name = f"chal_{challenge_id}_u_{user_id}"

    # Reuse container if active
    if container_name in container_map:
        return container_map[container_name]['url']

    image = f"ctf_challenge_{challenge_id}"
    container = client.containers.run(
        image=image,
        name=container_name,
        detach=True,
        ports={'80/tcp': None},
        user='1000:1000',
        network_mode='bridge',
        remove=False,  # Don't auto-remove so we can stop it manually
        cap_drop=['ALL'],
        mem_limit='256m',
        pids_limit=100,
        security_opt=['no-new-privileges'],
    )

    container.reload()
    port = container.attrs['NetworkSettings']['Ports']['80/tcp'][0]['HostPort']
    host = os.getenv('CTF_CONTAINER_HOST', 'localhost')
    url = f"http://{host}:{port}"

    container_map[container_name] = {
        'url': url,
        'timestamp': time.time(),
        'id': container.id
    }

    return url

def cleanup_expired_containers():
    now = time.time()
    to_remove = []
    for name, meta in container_map.items():
        if now - meta['timestamp'] > TIMEOUT_SECONDS:
            try:
                container = client.containers.get(meta['id'])
                container.stop()
            except Exception as e:
                print(f"Error stopping {name}: {e}")
            to_remove.append(name)
    for name in to_remove:
        container_map.pop(name)
