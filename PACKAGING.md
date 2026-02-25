# AIOS PyPI Package Preparation

## ✅ Completed

### 1. Package Structure
- [x] `setup.py` - setuptools configuration
- [x] `pyproject.toml` - modern Python packaging (PEP 621)
- [x] `__init__.py` - package entry point with AIOS class
- [x] `__main__.py` - CLI entry point (already existed)
- [x] `LICENSE` - MIT License
- [x] `.gitignore` - exclude generated files

### 2. Package Metadata
- **Name**: `aios-framework`
- **Version**: 0.5.0
- **Python**: >=3.8
- **License**: MIT
- **Author**: Shanhuhai
- **URL**: https://github.com/yangfei222666-9/aios

### 3. Dependencies
**Core**:
- pyyaml>=6.0
- watchdog>=3.0.0
- fastapi>=0.104.0
- uvicorn>=0.24.0
- websockets>=12.0

**Dev** (optional):
- pytest>=7.4.0
- pytest-asyncio>=0.21.0
- black>=23.0.0
- flake8>=6.0.0
- mypy>=1.5.0

### 4. Entry Points
- CLI: `aios` command (via `aios.__main__:main`)
- Python API: `from aios import AIOS`

### 5. Package Data
Included:
- config.yaml
- data/*.json, data/*.jsonl
- dashboard/templates/*.html
- dashboard/static/*.css, dashboard/static/*.js

---

## 📦 Next Steps

### 1. Test Local Install
```bash
cd C:\Users\A\.openclaw\workspace\aios
pip install -e .
```

### 2. Build Distribution
```bash
pip install build
python -m build
```
This creates:
- `dist/aios-framework-0.5.0.tar.gz` (source)
- `dist/aios_framework-0.5.0-py3-none-any.whl` (wheel)

### 3. Test Installation
```bash
pip install dist/aios_framework-0.5.0-py3-none-any.whl
aios version
python -c "from aios import AIOS; print(AIOS.__doc__)"
```

### 4. Upload to PyPI (when ready)
```bash
pip install twine
twine check dist/*
twine upload dist/*
```

---

## 🎯 Usage After Install

### CLI
```bash
aios health          # Health check
aios version         # Show version
aios insight         # Daily report
aios reflect         # Morning reflection
```

### Python API
```python
from aios import AIOS

# Initialize
system = AIOS()

# Log events
system.log_event("error", "network", {"code": 502, "url": "api.example.com"})

# Run pipeline
result = system.run_pipeline()

# Check evolution
score = system.evolution_score()
print(f"Evolution: {score['score']} ({score['grade']})")

# Handle complex tasks
system.handle_task("Analyze this codebase and suggest optimizations")
```

---

## 🚨 Before Publishing

### Required
- [ ] Test local install (`pip install -e .`)
- [ ] Test CLI commands (`aios health`, `aios version`)
- [ ] Test Python API import
- [ ] Build distribution (`python -m build`)
- [ ] Test wheel install
- [ ] Run tests (`pytest tests/`)

### Optional (but recommended)
- [ ] Add CHANGELOG.md
- [ ] Add CONTRIBUTING.md
- [ ] Add more examples in README
- [ ] Add badges (version, tests, license)
- [ ] Set up GitHub Actions for CI/CD
- [ ] Create GitHub release

---

## 📝 Notes

### Why `aios-framework` not `aios`?
- `aios` might be taken on PyPI
- `-framework` makes it clear what it is
- Can always claim `aios` later if available

### Why both setup.py and pyproject.toml?
- `pyproject.toml` is modern standard (PEP 621)
- `setup.py` for backward compatibility
- Both point to same metadata

### Package Size
Current estimate: ~500KB (code + config + dashboard)
- No large dependencies
- No bundled models
- Fast install

---

## 🎉 Ready to Test

Run this to test local install:
```bash
cd C:\Users\A\.openclaw\workspace\aios
pip install -e .
aios version
```
