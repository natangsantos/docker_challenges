from CTFd.models import Challenges, db
from CTFd.utils import get_config
from .utils import launch_secure_container, cleanup_expired_containers

class DockerChallenge(Challenges):
    __mapper_args__ = {"polymorphic_identity": "docker"}
    id = db.Column(db.Integer, db.ForeignKey("challenges.id"), primary_key=True)
    docker_image = db.Column(db.String(128))
    docker_command = db.Column(db.String(256))
    docker_ports = db.Column(db.String(128))  # Comma-separated ports
    
    def __init__(self, *args, **kwargs):
        super(DockerChallenge, self).__init__(**kwargs)
        self.type = "docker"
    
    @property
    def html(self):
        return f"""
        <button class="btn btn-info launch-docker" data-id="{self.id}">
            Launch Container
        </button>
        <div id="docker-info-{self.id}"></div>
        """
    
    def attempt(self, user):
        # Launch container when user attempts challenge
        container_url = launch_secure_container(self.id, user.id)
        return False, f"Container launched at {container_url}"