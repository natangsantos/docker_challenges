from flask import Blueprint
from CTFd.plugins import register_admin_plugin_menu_bar
from CTFd.plugins.challenges import CHALLENGE_CLASSES
from .models import DockerChallenge
from .views import admin_docker_challenges

def docker_challenges_override(app):
    # Register the challenge type
    CHALLENGE_CLASSES["docker"] = DockerChallenge
    
    # Create admin blueprint
    blueprint = Blueprint(
        "docker_challenges",
        __name__,
        template_folder="templates",
        static_folder="static"
    )
    
    # Add admin route
    blueprint.add_url_rule(
        "/admin/docker",
        view_func=admin_docker_challenges
    )
    
    # Register blueprint
    app.register_blueprint(blueprint)
    
    # Add admin menu item
    register_admin_plugin_menu_bar(
        title="Docker",
        route="/admin/docker"
    )