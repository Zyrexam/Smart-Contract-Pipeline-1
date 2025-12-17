"""
Check what solc versions are available in Docker images
"""

from stage_3.docker_executor import DockerExecutor
from stage_3.tool_loader import load_tool

docker = DockerExecutor(verbose=False)

print("=" * 80)
print("Checking Slither Docker Image")
print("=" * 80)

# Run a command to check solc versions
slither_config = load_tool("slither")
config_dict = slither_config.to_dict()
config_dict['solidity']['entrypoint'] = "ls -la /usr/local/bin/ | grep solc"

try:
    exit_code, logs, output = docker.execute(
        "// dummy",
        config_dict,
        timeout=30
    )
    print("\nAvailable solc-related binaries:")
    for line in logs:
        print(f"  {line}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 80)
print("Checking Mythril Docker Image")
print("=" * 80)

mythril_config = load_tool("mythril")
config_dict = mythril_config.to_dict()
config_dict['solidity']['entrypoint'] = "ls -la /usr/local/bin/ | grep -E '(solc|myth)'"

try:
    exit_code, logs, output = docker.execute(
        "// dummy",
        config_dict,
        timeout=30
    )
    print("\nAvailable binaries:")
    for line in logs:
        print(f"  {line}")
except Exception as e:
    print(f"Error: {e}")

# Try to check solc-select versions
print("\n" + "=" * 80)
print("Checking solc-select in Slither")
print("=" * 80)

config_dict = slither_config.to_dict()
config_dict['solidity']['entrypoint'] = "solc-select versions 2>&1 || echo 'solc-select not found'"

try:
    exit_code, logs, output = docker.execute(
        "// dummy",
        config_dict,
        timeout=30
    )
    print("\nsolc-select output:")
    for line in logs:
        print(f"  {line}")
except Exception as e:
    print(f"Error: {e}")
