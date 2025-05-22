import docker
import os
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_docker_client():
    try:
        return docker.DockerClient(
            base_url='unix:///var/run/docker.sock',
            version='1.40',
            timeout=60
        )
    except docker.errors.DockerException as e:
        print(f"Docker connection error: {e}")
        raise

client = get_docker_client()
container_map = {}
TIMEOUT_SECONDS = 1800

def launch_secure_container(challenge_id, user_id):
    container_name = f"chal_{challenge_id}_u_{user_id}"
    
    if container_name in container_map:
        if client.containers.get(container_map[container_name]['id']).status == 'running':
            return container_map[container_name]['url']
        else:
            container_map.pop(container_name)

    try:
        container = client.containers.run(
            image=f"ctf_challenge_{challenge_id}",
            name=container_name,
            detach=True,
            ports={'80/tcp': None},
            user='nobody:nogroup',  # More secure than UID
            network_mode='bridge',
            remove=False,
            cap_drop=['ALL'],
            mem_limit='256m',
            pids_limit=100,
            security_opt=['no-new-privileges'],
            read_only=True,
            tmpfs={'/tmp': 'rw,noexec,nosuid,size=16m'},
            cpu_period=100000,
            cpu_quota=50000,
        )
        
        container.reload()
        port = container.attrs['NetworkSettings']['Ports']['80/tcp'][0]['HostPort']
        url = f"http://{os.getenv('CTF_CONTAINER_HOST', 'localhost')}:{port}"
        
        container_map[container_name] = {
            'url': url,
            'timestamp': time.time(),
            'id': container.id
        }
        
        return url
    except Exception as e:
        print(f"Failed to launch container: {str(e)}")
        raise

def cleanup_expired_containers():
    now = time.time()
    expired = [n for n, m in container_map.items() if now - m['timestamp'] > TIMEOUT_SECONDS]
    
    for name in expired:
        try:
            container = client.containers.get(container_map[name]['id'])
            container.stop(timeout=10)
            container.remove()
            container_map.pop(name)
        except Exception as e:
            print(f"Cleanup failed for {name}: {str(e)}")
            try:
                client.api.remove_container(container_map[name]['id'], force=True)
            except:
                pass
            container_map.pop(name)