# Custom Docker Images for Stage 3

## Purpose

Pre-built Docker images with Solidity compilers installed to avoid:
- Network errors (403, checksum mismatches)
- Slow downloads during analysis
- Version compatibility issues

## Images

### custom-slither:latest
- Base: `smartbugs/slither:0.11.3`
- Solc versions: 0.8.20, 0.8.24, 0.8.25, 0.8.26
- Default: 0.8.20

### custom-mythril:latest
- Base: `smartbugs/mythril:0.24.7`
- Solc versions: 0.8.20, 0.8.24
- Default: 0.8.20

## Building

```bash
cd stage_3/docker
chmod +x build.sh
./build.sh
```

## Updating Tool Configs

After building, update the tool configurations:

### Slither
Edit `stage_3/tools/slither/config.yaml`:
```yaml
image: custom-slither:latest  # Changed from smartbugs/slither:0.11.3
```

### Mythril
Edit `stage_3/tools/mythril/config.yaml`:
```yaml
image: custom-mythril:latest  # Changed from smartbugs/mythril:0.24.7
```

## Testing

```bash
cd stage_3
python -m stage_3.test
```

Expected output:
```
• slither... ✓ (5-8 issues)
• mythril... ✓ (3-6 issues)
• semgrep... ✓ (3-5 issues)
• solhint... ✓ (13-15 issues)
```

## Updating

When new Solidity versions are released:

1. Edit Dockerfiles to add new versions
2. Rebuild: `./build.sh`
3. Test: `python -m stage_3.test`

## Troubleshooting

### Build fails
- Ensure Docker Desktop is running
- Check internet connection (for base image pull)
- Try: `docker system prune -a` to clean cache

### Images not found in test
- Verify images exist: `docker images | grep custom-`
- Check tool configs use correct image names

### Still getting network errors
- Verify environment variables in Dockerfiles
- Check if base images are correct versions
