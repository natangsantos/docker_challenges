from flask import render_template, request, jsonify
from CTFd.utils.decorators import admins_only
from .models import DockerChallenge
from .utils import get_running_containers

@blueprint.route('/containers', methods=['GET'])
def get_containers():
    containers = get_running_containers()
    return render_template('admin_docker_challenges.html', containers=containers)

@blueprint.route('/containers/<string:container_id>/stop', methods=['POST'])
def stop_container(container_id):
    try:
        container = client.containers.get(container_id)
        container.stop(timeout=10)
        container.remove()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500