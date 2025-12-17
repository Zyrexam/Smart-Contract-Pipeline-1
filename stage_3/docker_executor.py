"""
Docker Executor
===============

SmartBugs-inspired Docker execution for security tools.
Handles Windows compatibility by running tools in Docker containers.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Tuple, List

try:
    import docker
    import docker.errors
    import requests
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False


class DockerExecutor:
    """Execute security tools in Docker containers (SmartBugs-style)"""
    
    _client = None
    
    def __init__(self, verbose: bool = False):
        """Initialize Docker client"""
        self.verbose = verbose
        if not DOCKER_AVAILABLE:
            raise RuntimeError("Docker Python library not installed. Run: pip install docker")
        
        try:
            self._client = docker.from_env()
            self._client.info()  # Test connection
        except Exception as e:
            raise RuntimeError(f"Docker not available: {e}. Is Docker installed and running?")
    
    def execute(
        self,
        solidity_code: str,
        tool_config: dict,
        timeout: int = 120
    ) -> Tuple[Optional[int], List[str], Optional[bytes]]:
        """
        Execute tool in Docker container
        
        Args:
            solidity_code: Solidity source code
            tool_config: Tool configuration dict (from YAML)
            timeout: Timeout in seconds
        
        Returns:
            (exit_code, logs, output_bytes)
        """
        # Create temporary directory (like SmartBugs __docker_volume)
        sbdir = tempfile.mkdtemp()
        
        
        try:
            # Write contract file
            contract_filename = "contract.sol"
            contract_path = os.path.join(sbdir, contract_filename)
            with open(contract_path, "w", encoding="utf8") as f:
                f.write(solidity_code)
            
            # Copy scripts/bin if specified (like SmartBugs __docker_volume)
            bin_dest = os.path.join(sbdir, "bin")
            if tool_config.get("bin"):
                tool_id = tool_config.get("id", "unknown")
                # Get absolute path to scripts directory
                # docker_executor.py is in stage_3/, so tools/ is in stage_3/tools/
                script_dir_name = tool_config["bin"]  # Usually "scripts"
                current_file_dir = os.path.dirname(os.path.abspath(__file__))  # stage_3/
                bin_source = os.path.join(current_file_dir, "tools", tool_id, script_dir_name)
                
                if os.path.exists(bin_source):
                    # Copy entire scripts directory to /sb/bin
                    if os.path.exists(bin_dest):
                        shutil.rmtree(bin_dest)
                    shutil.copytree(bin_source, bin_dest)
                    # Make scripts executable (important for Linux containers)
                    # Note: os.chmod on Windows doesn't work the same, but Docker will handle it
                    try:
                        for root, dirs, files in os.walk(bin_dest):
                            for file in files:
                                file_path = os.path.join(root, file)
                                # Try to make executable (may not work on Windows, but Docker will handle it)
                                try:
                                    os.chmod(file_path, 0o755)  # rwxr-xr-x
                                except (OSError, AttributeError):
                                    pass  # Windows doesn't support chmod the same way
                    except Exception:
                        pass  # Continue even if chmod fails
                else:
                    # Scripts directory not found - create empty bin
                    os.makedirs(bin_dest, exist_ok=True)
                    if self.verbose:
                        print(f"    [WARN] Scripts directory not found: {bin_source}")
            else:
                # Create empty bin directory
                os.makedirs(bin_dest, exist_ok=True)
            
            # Get Docker image
            image = tool_config.get("image")
            if not image:
                raise ValueError(f"Tool {tool_config.get('id')} has no Docker image specified")
            
            # Ensure image is loaded
            self._ensure_image(image)
            
            # Build command (like SmartBugs - use command, not entrypoint)
            command = self._build_command(tool_config, contract_filename, timeout, "/sb/bin")
            
            # Debug: Check if scripts were copied
            if self.verbose:
                bin_path = os.path.join(sbdir, "bin")
                if os.path.exists(bin_path):
                    scripts = os.listdir(bin_path)
                    print(f"    [DEBUG] Scripts copied to /sb/bin: {scripts}")
                else:
                    print(f"    [DEBUG] WARNING: /sb/bin directory not found!")
            
            # Prepare Docker run arguments (like SmartBugs)
            # Use shell interpretation for string commands
            docker_args = {
                "image": image,
                "volumes": {sbdir: {"bind": "/sb", "mode": "rw"}},
                "command": ["/bin/sh", "-c", command],
                "detach": True,
                "user": "root",
                "working_dir": "/sb",
                "environment": {
                    "SOLC_SELECT_DISABLED": "1",
                    "MYTHRIL_DISABLE_SOLC_DOWNLOAD": "1",
                    "SOLC_VERSION": "0.8.20",
                },
                "network_mode": "bridge",  # Allow network but with limits
            }
            
            # Execute container
            container = None
            exit_code = None
            logs = []
            output = None
            
            try:
                container = self._client.containers.run(**docker_args)
                
                try:
                    result = container.wait(timeout=timeout)
                    exit_code = result["StatusCode"]
                except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                    # Timeout
                    try:
                        container.stop(timeout=10)
                    except docker.errors.APIError:
                        pass
                    exit_code = None
                
                # Get logs
                logs_bytes = container.logs()
                logs = logs_bytes.decode("utf8", errors="replace").splitlines()
                
                # Get output file if specified
                output_path = tool_config.get("output")
                if output_path:
                    try:
                        # Try to get file as tar archive
                        tar_stream, stat = container.get_archive(output_path)
                        # Read all chunks
                        output_chunks = []
                        for chunk in tar_stream:
                            output_chunks.append(chunk)
                        output = b"".join(output_chunks)
                    except docker.errors.NotFound:
                        # File not found, output might be in logs
                        output = None
                    except Exception as e:
                        # Other error, try reading from logs
                        output = None
            
            finally:
                # Cleanup container
                if container:
                    try:
                        container.kill()
                    except Exception:
                        pass
                    try:
                        container.remove()
                    except Exception:
                        pass
            
            return exit_code, logs, output
        
        finally:
            # Cleanup temp directory
            try:
                shutil.rmtree(sbdir)
            except Exception:
                pass
    
    def _ensure_image(self, image: str) -> None:
        """Ensure Docker image is available"""
        try:
            images = self._client.images.list(image)
            if not images:
                # Pull image
                print(f"  📦 Pulling Docker image: {image}")
                self._client.images.pull(image)
        except Exception as e:
            raise RuntimeError(f"Failed to load Docker image {image}: {e}")
    
    def _build_command(
        self,
        tool_config: dict,
        filename: str,
        timeout: int,
        bin_path: str
    ) -> str:
        """Build command string from config (like SmartBugs)"""
        solidity_config = tool_config.get("solidity", {})
        entrypoint_template = solidity_config.get("entrypoint", "")
        
        if not entrypoint_template:
            raise ValueError(f"Tool {tool_config.get('id')} has no entrypoint specified")
        
        # The template has quotes: '$BIN/do_solidity.sh' '$FILENAME' '$TIMEOUT' '$BIN'
        # We need to replace INCLUDING the quotes and dollar sign
        
        # Replace each variable pattern (with quotes)
        command = entrypoint_template.replace("'$FILENAME'", f"'/sb/{filename}'")
        command = command.replace("'$TIMEOUT'", f"'{timeout}'")
        command = command.replace("'$BIN'", f"'{bin_path}'")
        command = command.replace("'$MAIN'", "'0'")
        
        # Also handle unquoted versions just in case
        command = command.replace("$FILENAME", f"/sb/{filename}")
        command = command.replace("$TIMEOUT", str(timeout))
        command = command.replace("$BIN", bin_path)
        command = command.replace("$MAIN", "0")
        
        if self.verbose:
            print(f"    [DEBUG] Command template: {entrypoint_template}")
            print(f"    [DEBUG] Command after substitution: {command}")
        
        return command

