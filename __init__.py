from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from CTFd.utils.decorators import admins_only, authed_only

from CTFd.utils.user import get_current_user, get_current_team
from CTFd.utils import config as ctfd_config
from CTFd.models import db, Challenges, Solves, Fails, Flags, Tags, Files, ChallengeFiles, Hints, Awards # Import necessary models
from CTFd.plugins.challenges import BaseChallenge, CHALLENGE_CLASSES
from CTFd.plugins.flags import get_flag_class
import datetime

# Import the docker utility functions
from . import docker_utils
import logging

log = logging.getLogger(__name__)

# --- Plugin Configuration ---
PLUGIN_NAME = "Docker Container Manager"
PLUGIN_FOLDER = "docker_challenges" # Should match the directory name

# --- Database Models (Optional, if needed for storing container info) ---
# Example:
# class DockerChallengeContainers(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
#     team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
#     challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id'))
#     container_id = db.Column(db.String(128), unique=True)
#     ip_address = db.Column(db.String(128))
#     port = db.Column(db.Integer)
#     created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
#     expires = db.Column(db.DateTime) # For timeout
#
#     user = db.relationship('Users', foreign_keys="DockerChallengeContainers.user_id", lazy='select')
#     team = db.relationship('Teams', foreign_keys="DockerChallengeContainers.team_id", lazy='select')
#     challenge = db.relationship('Challenges', foreign_keys="DockerChallengeContainers.challenge_id", lazy='select')
#
#     def __init__(self, user_id, team_id, challenge_id, container_id, ip_address, port, expires):
#         self.user_id = user_id
#         self.team_id = team_id
#         self.challenge_id = challenge_id
#         self.container_id = container_id
#         self.ip_address = ip_address
#         self.port = port
#         self.expires = expires


# --- Custom Challenge Type (Recommended Approach) ---
# Define a new challenge type that uses Docker
class DockerChallengeType(BaseChallenge):
    id = "docker" # Unique identifier for the challenge type
    name = "docker" # Name displayed in the UI
    templates = { # Templates used for viewing/updating challenges of this type
        'create': 'admin/docker_challenge_create.html',
        'update': 'admin/docker_challenge_update.html',
        'view': 'user/docker_challenge_view.html',
    }
    scripts = { # Scripts used for viewing/updating challenges of this type
        'create': 'js/docker_challenge_create.js',
        'update': 'js/docker_challenge_update.js',
        'view': 'js/docker_challenge_view.js',
    }
    # Route specifies where the plugin serves assets from
    route = f'/plugins/{PLUGIN_FOLDER}/assets/'
    # Blueprint used to access the static_folder directory.
    blueprint = None # Will be set in load()

    @staticmethod
    def create(request):
        """
        This method is used to process the challenge creation request.
        It reads data from the request, creates a new challenge, and adds it to the database.
        """
        data = request.form or request.get_json()
        # Create challenge with basic info
        challenge = Challenges(**data)

        # Handle custom Docker type data
        type_data = challenge.type_data or {}
        type_data['docker_image'] = data.get('docker_image')
        type_data['docker_ports'] = data.get('docker_ports')
        type_data['docker_env'] = data.get('docker_env')
        type_data['docker_cpu_limit'] = data.get('docker_cpu_limit')
        type_data['docker_mem_limit'] = data.get('docker_mem_limit')
        type_data['docker_timeout'] = data.get('docker_timeout', 3600)
        challenge.type_data = type_data
        challenge.type = DockerChallengeType.id # Ensure type is set

        db.session.add(challenge)
        db.session.commit()
        return challenge

    @staticmethod
    def read(challenge):
        """
        This method is used to grab challenge information from the DB,
        including custom Docker fields stored in type_data.
        """
        challenge = Challenges.query.filter_by(id=challenge.id).first()
        # Ensure type_data is a dictionary
        type_data = challenge.type_data if isinstance(challenge.type_data, dict) else {}
        data = {
            'id': challenge.id,
            'name': challenge.name,
            'value': challenge.value,
            'description': challenge.description,
            'category': challenge.category,
            'state': challenge.state,
            'max_attempts': challenge.max_attempts,
            'type': challenge.type,
            'type_data': type_data, # Keep the raw type_data
            # Add custom fields specific to Docker challenges for easier access
            'docker_image': type_data.get('docker_image', ''),
            'docker_ports': type_data.get('docker_ports', ''), # e.g., "80:8080, 22:2222"
            'docker_env': type_data.get('docker_env', ''), # e.g., "VAR1=val1,VAR2=val2"
            'docker_cpu_limit': type_data.get('docker_cpu_limit', ''),
            'docker_mem_limit': type_data.get('docker_mem_limit', ''),
            'docker_timeout': type_data.get('docker_timeout', 3600) # Default 1 hour
        }
        return data

    @staticmethod
    def update(challenge, request):
        """
        This method is used to update the information associated with a challenge,
        including standard fields and custom Docker fields in type_data.
        """
        data = request.form or request.get_json()
        for attr, value in data.items():
            # Update standard challenge attributes
            if hasattr(challenge, attr) and attr not in ['id', 'type_data']:
                setattr(challenge, attr, value)

        # Update custom Docker challenge type data
        type_data = challenge.type_data if isinstance(challenge.type_data, dict) else {}
        type_data['docker_image'] = data.get('docker_image')
        type_data['docker_ports'] = data.get('docker_ports')
        type_data['docker_env'] = data.get('docker_env')
        type_data['docker_cpu_limit'] = data.get('docker_cpu_limit')
        type_data['docker_mem_limit'] = data.get('docker_mem_limit')
        type_data['docker_timeout'] = data.get('docker_timeout')
        challenge.type_data = type_data # Make sure this is updated

        db.session.commit()
        return challenge

    @staticmethod
    def delete(challenge):
        """
        This method is used to delete the resources used by a challenge.
        Includes standard CTFd cleanup.
        """
        Fails.query.filter_by(challenge_id=challenge.id).delete()
        Solves.query.filter_by(challenge_id=challenge.id).delete()
        Flags.query.filter_by(challenge_id=challenge.id).delete()
        files = ChallengeFiles.query.filter_by(challenge_id=challenge.id).all()
        for f in files:
            # Add file deletion logic from storage if necessary
            pass
        ChallengeFiles.query.filter_by(challenge_id=challenge.id).delete()
        Tags.query.filter_by(challenge_id=challenge.id).delete()
        Hints.query.filter_by(challenge_id=challenge.id).delete()
        Awards.query.filter_by(challenge_id=challenge.id).delete()
        Challenges.query.filter_by(id=challenge.id).delete()
        db.session.commit()

    @staticmethod
    def attempt(challenge, request):
        """
        This method is used to check whether a given input is right.
        Standard flag checking logic.
        """
        data = request.form or request.get_json()
        submission = data["submission"].strip()

        flags = Flags.query.filter_by(challenge_id=challenge.id).all()

        for flag in flags:
            if get_flag_class(flag.type).compare(flag, submission):
                # Potentially stop container on correct solve?
                # stop_user_container(user.id, challenge.id) # Implement this function later
                return True, "Correct"

        return False, "Incorrect"

    @staticmethod
    def solve(user, team, challenge, request):
        """
        This method is used to process the solve.
        Standard solve processing.
        """
        super(DockerChallengeType, DockerChallengeType).solve(user, team, challenge, request)
        # Optionally stop container on solve
        # stop_user_container(user.id, challenge.id) # Implement this function later

    @staticmethod
    def fail(user, team, challenge, request):
        """
        This method is used to process the incorrect submission.
        Standard fail processing.
        """
        super(DockerChallengeType, DockerChallengeType).fail(user, team, challenge, request)


# --- CTFd Plugin Loading ---
def load(app):
    log.info(f"Loading {PLUGIN_NAME} plugin")
    app.db.create_all() # Create tables if they don't exist

    # Create blueprint for the challenge type FIRST
    challenge_bp = Blueprint(
        DockerChallengeType.id, # 'docker'
        __name__,
        template_folder="templates",
        static_folder="assets",
        url_prefix=DockerChallengeType.route # Serves static assets
    )
    DockerChallengeType.blueprint = challenge_bp # Assign to class

    # Register the challenge type class and its blueprint
    CHALLENGE_CLASSES[DockerChallengeType.id] = DockerChallengeType
    app.register_blueprint(challenge_bp)

    # --- Admin Configuration Route Function ---
    @admins_only
    def admin_config_page_func(): # Renamed function slightly for clarity
        if request.method == 'POST':
            # Save settings logic here (using CTFd.utils.config.set_config)
            # Example:
            # ctfd_config.set_config('docker_manager:docker_host', request.form.get('docker_host'))
            # ctfd_config.set_config('docker_manager:default_timeout', request.form.get('default_timeout'))
            flash(f'{PLUGIN_NAME} settings updated successfully!', 'success')
            # Use the correct endpoint name for url_for
            return redirect(url_for(f'{PLUGIN_FOLDER}_admin_config.admin_config_page_view'))

        # Load settings for display (using CTFd.utils.config.get_config)
        # Example:
        # config = {
        #     'docker_host': ctfd_config.get_config('docker_manager:docker_host'),
        #     'default_timeout': ctfd_config.get_config('docker_manager:default_timeout')
        # }
        config = {} # Placeholder
        return render_template("docker_manager_config.html", config=config)

    # Create and register the blueprint for admin configuration routes
    admin_bp = Blueprint(
        f'{PLUGIN_FOLDER}_admin_config', # More specific blueprint name
        __name__,
        template_folder="templates", # This blueprint also looks in 'templates'
        url_prefix=f'/admin/plugins/{PLUGIN_FOLDER}'
    )
    admin_bp.add_url_rule('', 'admin_config_page_view', admin_config_page_func, methods=['GET', 'POST'])
    app.register_blueprint(admin_bp)   # Register assets (No longer needed explicitly for challenge types with blueprints)
    # register_plugin_assets_directory(app, base_path=f'/plugins/{PLUGIN_FOLDER}/assets/')

    # Register admin menu bar link (No longer needed explicitly, handled by config.json route and blueprint)
    # register_admin_plugin_menu_bar(PLUGIN_NAME, f'/admin/plugins/{PLUGIN_FOLDER}')

    # Create and register the blueprint for admin configuration routes
    admin_bp = Blueprint(
        f'{PLUGIN_FOLDER}_admin_config', # More specific blueprint name
        __name__,
        template_folder="templates",
        url_prefix=f'/admin/plugins/{PLUGIN_FOLDER}'
    )
    # Add the rule using the function defined above and a specific endpoint name
    admin_bp.add_url_rule('', 'admin_config_page_view', admin_config_page_func, methods=['GET', 'POST'])
    app.register_blueprint(admin_bp)


    # --- API Endpoint for Starting Container (called from challenge view JS) ---
    @app.route(f'/plugins/{PLUGIN_FOLDER}/api/start_instance/<int:challenge_id>', methods=['POST'])
    @authed_only # Ensure user is logged in
    def start_instance_api(challenge_id):
        user = get_current_user()
        challenge = Challenges.query.filter_by(id=challenge_id).first_or_404()

        if challenge.type != DockerChallengeType.id:
            log.warning(f"User {user.id} attempted to start non-docker challenge {challenge_id}")
            return {"success": False, "message": "Challenge is not a Docker challenge."}, 400

        # --- Get Docker Client --- (Read host from config later)
        # docker_host = ctfd_config.get_config('docker_manager:docker_host')
        docker_host = None # Use default from environment for now
        client = docker_utils.get_docker_client(docker_host)
        if not client:
            log.error("Failed to get Docker client for starting instance.")
            return {"success": False, "message": "Failed to connect to Docker service. Please contact an admin."}, 500

        # --- Get Challenge Config --- (Using the read method)
        challenge_data = DockerChallengeType.read(challenge)
        image_name = challenge_data.get('docker_image')
        ports_str = challenge_data.get('docker_ports', '') # e.g., "80:8080, 22:2222/udp"
        env_str = challenge_data.get('docker_env', '') # e.g., "VAR1=val1,VAR2=val2"
        cpu_limit = challenge_data.get('docker_cpu_limit')
        mem_limit = challenge_data.get('docker_mem_limit')
        # timeout = challenge_data.get('docker_timeout', 3600) # Need to handle timeout later

        if not image_name:
            log.error(f"Docker image not configured for challenge {challenge_id}")
            return {"success": False, "message": "Docker image not configured for this challenge."}, 500

        # --- Parse Ports --- (Improved parsing)
        ports_config = {}
        if ports_str:
            try:
                for port_map in ports_str.split(','):
                    if not port_map.strip(): continue
                    parts = port_map.strip().split(':')
                    container_port_proto = parts[0]
                    host_port = int(parts[1]) if len(parts) > 1 and parts[1] else None # None for dynamic assignment
                    if '/' not in container_port_proto:
                        container_port_proto += '/tcp' # Default to TCP
                    ports_config[container_port_proto] = host_port
            except Exception as e:
                log.error(f"Error parsing ports string '{ports_str}' for challenge {challenge_id}: {e}")
                return {"success": False, "message": f"Invalid port mapping format: {ports_str}"}, 500

        # --- Parse Environment Variables --- (Improved parsing)
        env_vars = {}
        if env_str:
            try:
                for env_pair in env_str.split(','):
                    if not env_pair.strip(): continue
                    key, value = env_pair.strip().split('=', 1)
                    env_vars[key] = value
            except Exception as e:
                log.error(f"Error parsing environment variables string '{env_str}' for challenge {challenge_id}: {e}")
                return {"success": False, "message": f"Invalid environment variable format: {env_str}"}, 500

        # --- Start Container --- (Using docker_utils)
        log.info(f"User {user.id} starting instance for challenge {challenge_id} with image {image_name}")
        container = docker_utils.start_challenge_container(
            client=client,
            image_name=image_name,
            user_id=user.id,
            challenge_id=challenge.id,
            ports_config=ports_config,
            env_vars=env_vars,
            cpu_limit=cpu_limit,
            mem_limit=mem_limit
        )

        if not container:
            log.error(f"Failed to start container for user {user.id}, challenge {challenge_id}")
            return {"success": False, "message": "Failed to start challenge instance. Please try again or contact an admin."}, 500

        # --- Get Connection Info --- (Improved logic)
        try:
            container.reload() # Ensure attributes are up-to-date
            attrs = container.attrs
            connection_info = {}
            display_info_parts = []

            # Extract mapped ports
            if ports_config:
                for container_port_proto, _ in ports_config.items():
                    host_ip, host_port = docker_utils.get_container_ip_port(attrs, container_port_proto)
                    if host_port:
                        # Determine the accessible host address
                        # This is tricky and depends on deployment.
                        # Using request.host assumes CTFd and Docker containers are accessible via the same domain/IP.
                        # A configurable public host/IP might be needed for Docker daemon running elsewhere.
                        display_host = request.host.split(':')[0]
                        connection_key = container_port_proto.split('/')[0] # Just the port number for display key
                        connection_value = f"{display_host}:{host_port}"
                        connection_info[connection_key] = connection_value
                        display_info_parts.append(f"<li>Port {container_port_proto}: <code>{connection_value}</code></li>")
                    else:
                        log.warning(f"Could not find host port mapping for {container_port_proto} in container {container.id}")

            # Store container info (e.g., in session or DB if needed for later management/timeout)
            # session[f'docker_instance_{challenge_id}'] = {'id': container.id, 'info': connection_info, 'expires': ...}

            display_html = f"Instance started successfully. Connect using:<ul>{''.join(display_info_parts)}</ul>"
            if not display_info_parts:
                display_html = "Instance started, but no mapped ports found to display connection info."

            return {
                "success": True,
                "message": "Challenge instance started successfully!",
                "connection_info": connection_info, # Dict: {'80': 'ctfd.example.com:32768'}
                "display_html": display_html # HTML formatted string for display
            }
        except Exception as e:
            log.exception(f"Error retrieving connection info for container {container.id}: {e}")
            # Attempt to stop the container if we can't get info
            docker_utils.stop_container(client, container.id)
            return {"success": False, "message": "Instance started but failed to retrieve connection details. Instance stopped."}, 500

    # --- API Endpoint for Stopping Container (Optional - Placeholder) ---
    # @app.route(f'/plugins/{PLUGIN_FOLDER}/api/stop_instance/<int:challenge_id>', methods=['POST'])
    # @authed_only
    # def stop_instance_api(challenge_id):
    #     user = get_current_user()
    #     # Retrieve container ID associated with user and challenge (from session or DB)
    #     # container_id = ...
    #     # client = docker_utils.get_docker_client(...)
    #     # success = docker_utils.stop_container(client, container_id)
    #     # return {"success": success}

    log.info(f"{PLUGIN_NAME} plugin loaded successfully.")


