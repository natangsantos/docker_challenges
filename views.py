from flask import render_template, request, jsonify
from CTFd.utils.decorators import admins_only
from .models import DockerChallenge
from .utils import get_running_containers

@admins_only
def admin_docker_challenges():
    if request.method == "GET":
        challenges = DockerChallenge.query.all()
        containers = get_running_containers()
        return render_template(
            "admin_docker_challenges.html",
            challenges=challenges,
            containers=containers
        )