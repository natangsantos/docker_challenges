from CTFd.plugins import register_plugin_assets_directory

print("🐳 Docker Challenges Plugin Loading!")  # DEBUG

def load(app):
    print("🔥 Initializing Docker Challenges Plugin!")  # DEBUG
    register_plugin_assets_directory(app, base_path="/plugins/docker_challenges/static/")
    
    try:
        from .plugin import docker_challenges_override
        docker_challenges_override(app)
        print("✅ Plugin initialized successfully!")
    except Exception as e:
        print(f"❌ Plugin initialization failed: {str(e)}")
        raise