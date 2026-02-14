"""
Falco Automated Response Service
Receives Falco events from Falcosidekick and executes response actions.

Part of test-hard security hardening platform.
"""

import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml
from flask import Flask, jsonify, request

import docker

app = Flask(__name__)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("falco-responder")

# Load response actions config
CONFIG_PATH = os.environ.get("RESPONSE_CONFIG", "/app/response_actions.yaml")
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"
DOCKER_HOST = os.environ.get("DOCKER_HOST", "unix:///var/run/docker.sock")

# Cooldown tracking: rule_name+container -> last_action_time
_cooldowns: dict[str, float] = {}


def load_config() -> dict:
    """Load response actions configuration."""
    config_path = Path(CONFIG_PATH)
    if not config_path.exists():
        logger.warning("Config file %s not found, using empty config", CONFIG_PATH)
        return {"defaults": {"dry_run": True, "log_all": True, "cooldown_seconds": 60}, "rules": {}}
    with open(config_path) as f:
        return yaml.safe_load(f)


def get_docker_client() -> docker.DockerClient:
    """Create Docker client."""
    try:
        return docker.DockerClient(base_url=DOCKER_HOST)
    except Exception as e:
        logger.error("Failed to connect to Docker: %s", e)
        raise


def is_cooled_down(rule_name: str, container_name: str, cooldown_seconds: int) -> bool:
    """Check if the cooldown period has passed for this rule+container."""
    key = f"{rule_name}:{container_name}"
    last_time = _cooldowns.get(key, 0)
    now = time.time()
    if now - last_time < cooldown_seconds:
        logger.info("Cooldown active for %s (%.0fs remaining)", key, cooldown_seconds - (now - last_time))
        return False
    _cooldowns[key] = now
    return True


def extract_event_fields(event: dict) -> dict:
    """Extract relevant fields from Falco event."""
    output_fields = event.get("output_fields", {})
    return {
        "rule": event.get("rule", "unknown"),
        "priority": event.get("priority", "unknown"),
        "output": event.get("output", ""),
        "time": event.get("time", ""),
        "tags": event.get("tags", []),
        "container_name": output_fields.get("container.name", ""),
        "container_id": output_fields.get("container.id", ""),
        "image": output_fields.get("container.image.repository", ""),
        "process": output_fields.get("proc.name", ""),
        "pid": output_fields.get("proc.pid", ""),
        "user": output_fields.get("user.name", ""),
        "file": output_fields.get("fd.name", ""),
    }


def action_log(fields: dict, action_config: dict) -> dict:
    """Log the event."""
    message = action_config.get("message", "Falco event detected")
    logger.info(
        "[%s] %s | rule=%s container=%s process=%s user=%s",
        fields["priority"].upper(),
        message,
        fields["rule"],
        fields["container_name"],
        fields["process"],
        fields["user"],
    )
    return {"action": "log", "success": True, "message": message}


def action_kill_process(fields: dict, action_config: dict, dry_run: bool) -> dict:
    """Kill the offending process inside the container."""
    container_name = fields["container_name"]
    pid = fields.get("pid")
    if not container_name or not pid:
        return {"action": "kill_process", "success": False, "reason": "missing container_name or pid"}

    if dry_run:
        logger.info("[DRY RUN] Would kill PID %s in container %s", pid, container_name)
        return {"action": "kill_process", "success": True, "dry_run": True}

    try:
        client = get_docker_client()
        container = client.containers.get(container_name)
        container.exec_run(f"kill -9 {pid}", privileged=True)
        logger.warning("Killed PID %s in container %s", pid, container_name)
        return {"action": "kill_process", "success": True, "pid": pid, "container": container_name}
    except Exception as e:
        logger.error("Failed to kill process: %s", e)
        return {"action": "kill_process", "success": False, "error": str(e)}


def action_pause_container(fields: dict, action_config: dict, dry_run: bool) -> dict:
    """Pause the container."""
    container_name = fields["container_name"]
    if not container_name:
        return {"action": "pause_container", "success": False, "reason": "missing container_name"}

    if dry_run:
        logger.info("[DRY RUN] Would pause container %s", container_name)
        return {"action": "pause_container", "success": True, "dry_run": True}

    try:
        client = get_docker_client()
        container = client.containers.get(container_name)
        container.pause()
        logger.warning("Paused container %s", container_name)
        return {"action": "pause_container", "success": True, "container": container_name}
    except Exception as e:
        logger.error("Failed to pause container: %s", e)
        return {"action": "pause_container", "success": False, "error": str(e)}


def action_stop_container(fields: dict, action_config: dict, dry_run: bool) -> dict:
    """Stop the container."""
    container_name = fields["container_name"]
    if not container_name:
        return {"action": "stop_container", "success": False, "reason": "missing container_name"}

    if dry_run:
        logger.info("[DRY RUN] Would stop container %s", container_name)
        return {"action": "stop_container", "success": True, "dry_run": True}

    try:
        client = get_docker_client()
        container = client.containers.get(container_name)
        container.stop(timeout=10)
        logger.warning("Stopped container %s", container_name)
        return {"action": "stop_container", "success": True, "container": container_name}
    except Exception as e:
        logger.error("Failed to stop container: %s", e)
        return {"action": "stop_container", "success": False, "error": str(e)}


def action_network_isolate(fields: dict, action_config: dict, dry_run: bool) -> dict:
    """Disconnect the container from all networks."""
    container_name = fields["container_name"]
    if not container_name:
        return {"action": "network_isolate", "success": False, "reason": "missing container_name"}

    if dry_run:
        logger.info("[DRY RUN] Would isolate container %s from all networks", container_name)
        return {"action": "network_isolate", "success": True, "dry_run": True}

    try:
        client = get_docker_client()
        container = client.containers.get(container_name)
        networks = container.attrs.get("NetworkSettings", {}).get("Networks", {})
        disconnected = []
        for network_name in networks:
            try:
                network = client.networks.get(network_name)
                network.disconnect(container)
                disconnected.append(network_name)
            except Exception as e:
                logger.error("Failed to disconnect from network %s: %s", network_name, e)
        logger.warning("Isolated container %s from networks: %s", container_name, disconnected)
        return {"action": "network_isolate", "success": True, "container": container_name, "disconnected": disconnected}
    except Exception as e:
        logger.error("Failed to isolate container: %s", e)
        return {"action": "network_isolate", "success": False, "error": str(e)}


def action_alert(fields: dict, action_config: dict) -> dict:
    """Log an alert message (additional alerts are routed via Falcosidekick -> Alertmanager)."""
    message = action_config.get("message", "Alert triggered")
    logger.warning(
        "[ALERT] %s | rule=%s container=%s image=%s user=%s",
        message,
        fields["rule"],
        fields["container_name"],
        fields["image"],
        fields["user"],
    )
    return {"action": "alert", "success": True, "message": message}


# Action dispatcher
ACTION_HANDLERS = {
    "log": action_log,
    "kill_process": action_kill_process,
    "pause_container": action_pause_container,
    "stop_container": action_stop_container,
    "network_isolate": action_network_isolate,
    "alert": action_alert,
}


def process_event(event: dict) -> dict:
    """Process a Falco event and execute configured response actions."""
    config = load_config()
    defaults = config.get("defaults", {})
    rules_config = config.get("rules", {})
    global_dry_run = DRY_RUN or defaults.get("dry_run", False)
    cooldown_seconds = defaults.get("cooldown_seconds", 60)

    fields = extract_event_fields(event)
    rule_name = fields["rule"]
    container_name = fields["container_name"]

    # Always log if log_all is enabled
    if defaults.get("log_all", True):
        logger.info(
            "Event received: rule=%s priority=%s container=%s process=%s user=%s",
            rule_name, fields["priority"], container_name, fields["process"], fields["user"],
        )

    # Check if we have a response configured for this rule
    rule_config = rules_config.get(rule_name)
    if not rule_config:
        return {"status": "no_action", "rule": rule_name, "reason": "no response configured"}

    if not rule_config.get("enabled", True):
        return {"status": "disabled", "rule": rule_name}

    # Check cooldown
    if not is_cooled_down(rule_name, container_name, cooldown_seconds):
        return {"status": "cooldown", "rule": rule_name, "container": container_name}

    # Execute actions
    results = []
    for action_def in rule_config.get("actions", []):
        action_type = action_def.get("type", "log")
        handler = ACTION_HANDLERS.get(action_type)
        if not handler:
            logger.error("Unknown action type: %s", action_type)
            results.append({"action": action_type, "success": False, "error": "unknown action type"})
            continue

        try:
            if action_type in ("kill_process", "pause_container", "stop_container", "network_isolate"):
                result = handler(fields, action_def, global_dry_run)
            else:
                result = handler(fields, action_def)
            results.append(result)
        except Exception as e:
            logger.error("Action %s failed: %s", action_type, e)
            results.append({"action": action_type, "success": False, "error": str(e)})

    return {
        "status": "processed",
        "rule": rule_name,
        "container": container_name,
        "actions": results,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---- Flask Routes ----

@app.route("/respond", methods=["POST"])
def respond():
    """Handle incoming Falco events from Falcosidekick."""
    try:
        event = request.get_json(force=True)
        result = process_event(event)
        return jsonify(result), 200
    except Exception as e:
        logger.error("Error processing event: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "falco-responder",
        "dry_run": DRY_RUN,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }), 200


@app.route("/config", methods=["GET"])
def get_config():
    """Return current response configuration."""
    config = load_config()
    return jsonify(config), 200


@app.route("/events", methods=["GET"])
def get_recent_events():
    """Return cooldown state (active rules)."""
    now = time.time()
    config = load_config()
    cooldown_seconds = config.get("defaults", {}).get("cooldown_seconds", 60)
    active = {
        key: {
            "last_action": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
            "cooldown_remaining": max(0, cooldown_seconds - (now - ts)),
        }
        for key, ts in _cooldowns.items()
    }
    return jsonify({"active_cooldowns": active}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5080))
    logger.info("Starting Falco Responder on port %d (dry_run=%s)", port, DRY_RUN)
    app.run(host="0.0.0.0", port=port)
