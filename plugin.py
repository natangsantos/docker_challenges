from flask import Blueprint, jsonify
from CTFd.plugins import register_plugin_assets_directory
from CTFd.plugins.challenges import CHALLENGE_CLASSES
from CTFd.utils.user import get_current_user
from CTFd.utils.decorators import authed_only
from .models import DockerChallenge
from .scheduler import start_scheduler
from .utils import launch_secure_container

docker_challenge_bp = Blueprint('container_challenges', __name__)

@docker_challenge_bp.route('/plugins/container_challenges/launch/<int:challenge_id>', methods=['POST'])
@authed_only
def launch(challenge_id):
    user = get_current_user()
    url = launch_secure_container(challenge_id, user.id)
    return jsonify({'status': 'success', 'url': url})

def load(app=None):
    CHALLENGE_CLASSES['docker'] = DockerChallenge
    register_plugin_assets_directory(app, base_path='/plugins/container_challenges/')
    app.register_blueprint(docker_challenge_bp)
    start_scheduler()
