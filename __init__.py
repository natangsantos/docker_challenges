from CTFd.plugins import register_plugin_assets_directory

def load(app):
    register_plugin_assets_directory(app, base_path="/plugins/docker_challenges/static/")
    from .plugin import docker_challenges_override
    docker_challenges_override(app)