"""
Deep Debug - Check what's actually in the Docker output
"""

from stage_3.docker_executor import DockerExecutor
from stage_3.tool_loader import load_tool
import json

TEST_CODE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract VulnerableContract {
    mapping(address => uint256) public balances;
    
    function withdraw() public {
        uint256 amount = balances[msg.sender];
        (bool success,) = msg.sender.call{value: amount}("");
        require(success);
        balances[msg.sender] = 0;
    }
    
    function badAuth() public view returns (bool) {
        return tx.origin == msg.sender;
    }
    
    receive() external payable {
        balances[msg.sender] += msg.value;
    }
}
"""

print("=" * 80)
print("DEEP DEBUG - Checking Slither Output")
print("=" * 80)

docker = DockerExecutor(verbose=True)

# Test Slither
print("\n[SLITHER]")
print("-" * 80)
slither_config = load_tool("slither")
exit_code, logs, output = docker.execute(
    TEST_CODE,
    slither_config.to_dict(),
    timeout=120
)

print(f"\nExit code: {exit_code}")
print(f"Logs ({len(logs)} lines):")
for i, line in enumerate(logs[-20:], 1):
    print(f"  {i}: {line}")

if output:
    print(f"\nOutput size: {len(output)} bytes")
    # Try to extract from tar
    import tarfile
    import io
    try:
        with tarfile.open(fileobj=io.BytesIO(output)) as tar:
            print(f"Tar contents: {tar.getnames()}")
            for member in tar.getmembers():
                if member.name.endswith('.json'):
                    f = tar.extractfile(member)
                    if f:
                        content = f.read().decode('utf8')
                        print(f"\nJSON content from {member.name}:")
                        print(content[:500])
                        # Try to parse
                        try:
                            data = json.loads(content)
                            print(f"\nParsed JSON keys: {data.keys()}")
                            if 'results' in data:
                                print(f"Detectors: {len(data.get('results', {}).get('detectors', []))}")
                        except:
                            pass
    except Exception as e:
        print(f"Error extracting tar: {e}")

print("\n" + "=" * 80)
print("DEEP DEBUG - Checking Mythril Output")
print("=" * 80)

# Test Mythril
print("\n[MYTHRIL]")
print("-" * 80)
mythril_config = load_tool("mythril")
exit_code, logs, output = docker.execute(
    TEST_CODE,
    mythril_config.to_dict(),
    timeout=120
)

print(f"\nExit code: {exit_code}")
print(f"Logs ({len(logs)} lines):")
for i, line in enumerate(logs, 1):
    print(f"  {i}: {line}")

# Check if there's JSON in logs
for line in logs:
    if line.strip().startswith('{'):
        try:
            data = json.loads(line)
            print(f"\nFound JSON in logs:")
            print(f"Keys: {data.keys()}")
            if 'issues' in data:
                print(f"Issues: {len(data['issues'])}")
        except:
            pass
