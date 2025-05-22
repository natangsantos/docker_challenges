import docker
import time
from flask import current_app
from CTFd.models import Users

client = docker.DockerClient(base_url='unix:///var/run/docker.sock')

container_map = {}

def get_running_containers():
    results = []
    for name, meta in container_map.items():
        try:
            container = client.containers.get(meta['id'])
            user = Users.query.filter_by(id=meta['user_id']).first()
            
            results.append({
                'id': container.id,
                'challenge_id': meta['challenge_id'],
                'user_id': meta['user_id'],
                'username': user.name,
                'port': meta['port'],
                'uptime': time.strftime(
                    "%Hh %Mm %Ss",
                    time.gmtime(time.time() - meta['timestamp'])
                )
            })
        except:
            continue
    return results

def launch_secure_container(challenge_id, user_id):
    container_name = f"chal_{challenge_id}_u_{user_id}"
    
    # Reuse existing container if valid
    if container_name in container_map:
        container = client.containers.get(container_map[container_name]['id'])
        if container.status == 'running':
            return container_map[container_name]['url']
    
    # Get challenge config
    challenge = current_app.db.session.query(
        current_app.db.func.json_object_agg(
            'docker_image', DockerChallenge.docker_image,
            'docker_ports', DockerChallenge.docker_ports
        )
    ).filter(DockerChallenge.id == challenge_id).first()
    
    # Launch new container
    container = client.containers.run(
        image=challenge.docker_image,
        name=container_name,
        detach=True,
        ports={'80/tcp': None},
        network_mode='bridge',
        mem_limit='256m',
        cpu_period=100000,
        cpu_quota=50000,
        security_opt=['no-new-privileges'],
        cap_drop=['ALL']
    )
    
    # Get assigned port
    container.reload()
    port = container.attrs['NetworkSettings']['Ports']['80/tcp'][0]['HostPort']
    url = f"http://{current_app.config.get('HOSTNAME')}:{port}"
    
    # Store container info
    container_map[container_name] = {
        'id': container.id,
        'challenge_id': challenge_id,
        'user_id': user_id,
        'port': port,
        'url': url,
        'timestamp': time.time()
    }
    
    return url

def cleanup_expired_containers():
    current_time = time.time()
    for name, meta in list(container_map.items()):
        if current_time - meta['timestamp'] > 3600:  # 1 hour timeout
            try:
                container = client.containers.get(meta['id'])
                container.stop(timeout=10)
                container.remove()
            except:
                pass
            container_map.pop(name)