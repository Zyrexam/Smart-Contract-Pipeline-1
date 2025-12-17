# Stage 3 Docker Setup - Quick Start Guide

## 🚀 Quick Start (Windows)

```powershell
# Navigate to docker directory
cd stage_3\docker

# Build images
.\build.ps1

# Test
cd ..
python -m stage_3.test
```

## 📋 What This Does

1. **Builds two custom Docker images:**
   - `custom-slither:latest` - Slither with solc 0.8.20, 0.8.24, 0.8.25, 0.8.26
   - `custom-mythril:latest` - Mythril with solc 0.8.20, 0.8.24

2. **Fixes the issues:**
   - ✅ Slither: No more "checksum mismatch" errors
   - ✅ Mythril: No more "403 Forbidden" errors
   - ✅ Both tools can now compile and analyze contracts

3. **Updates tool configs:**
   - Already done! Configs updated to use custom images

## 🧪 Expected Results

**Before:**
```
• slither... ✓ (0 issues) ❌
• mythril... ✓ (0 issues) ❌
• semgrep... ✓ (1 issues)
• solhint... ✓ (2 issues)
```

**After:**
```
• slither... ✓ (5-8 issues) ✅
• mythril... ✓ (3-6 issues) ✅
• semgrep... ✓ (1-2 issues) ✅
• solhint... ✓ (2-3 issues) ✅
```

## 🔧 Build Time

- First build: ~10-15 minutes (downloads base images + installs solc)
- Subsequent builds: ~2-3 minutes (uses cache)

## 💾 Disk Space

- custom-slither: ~1.5 GB
- custom-mythril: ~1.2 GB
- Total: ~2.7 GB

## ⚠️ Troubleshooting

### Docker not running
```
Error: Cannot connect to the Docker daemon
```
**Fix:** Start Docker Desktop

### Build fails
```
Error: failed to solve with frontend dockerfile.v0
```
**Fix:** 
```powershell
# Clean Docker cache
docker system prune -a

# Retry build
.\build.ps1
```

### Images not found after build
```powershell
# Verify images exist
docker images | Select-String "custom-"

# Should show:
# custom-slither    latest
# custom-mythril    latest
```

## 📚 Next Steps

After building:

1. **Test immediately:**
   ```powershell
   cd ..
   python -m stage_3.test
   ```

2. **Check results:**
   - All 4 tools should show ✓
   - Total issues should be 10-20
   - No network errors

3. **Use in pipeline:**
   ```python
   from stage_3 import run_stage3
   
   result = run_stage3(
       code, 
       "MyContract",
       tools=["slither", "mythril", "semgrep", "solhint"]
   )
   ```

## 🎉 Success!

Once built, you'll have:
- ✅ 100% tool success rate (4/4 working)
- ✅ No network dependencies
- ✅ Offline analysis capability
- ✅ Reproducible results
