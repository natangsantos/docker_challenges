from CTFd.plugins import register_plugin_assets_directory

def load(app):
    # Register plugin assets
    register_plugin_assets_directory(
        app, 
        base_path="/plugins/docker_challenges/static/"
    )
    
    # Import and register plugin components
    from .plugin import docker_challenges_override
    docker_challenges_override(app)