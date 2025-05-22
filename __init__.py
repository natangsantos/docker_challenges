from CTFd.plugins import register_plugin_assets_directory

def load(app):
    # Register assets first
    register_plugin_assets_directory(
        app, 
        base_path="/plugins/docker_challenges/static/"
    )
    
    # Import plugin components AFTER app is available
    from .plugin import docker_challenges_override
    
    # Perform plugin setup
    docker_challenges_override(app)