# Changelog

All notable changes to AIOS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-02-23

### Added
- **PyPI packaging**: `pip install aios-framework` support
- **Python API**: `from aios import AIOS` for programmatic use
- **CLI commands**: `aios health`, `aios version`, `aios insight`, `aios reflect`
- **Production tools**: Dashboard (WebSocket real-time), watcher, tracker, budget, orchestrator, integrations
- **Multi-agent system**: Async spawn (600x speedup), circuit breaker (95% stability), smart routing
- **Self-healing pipeline**: sensors → alerts → reactor → verifier → convergence → feedback → evolution
- **Learning system**: Autolearn v1.1 with fuzzy matching and explainability
- **Documentation**: README v2.0, DEMO_SCRIPT.md, PACKAGING.md

### Changed
- Evolution score improved from 0.24 to 0.457 (healthy)
- Agent spawn time reduced from 180s to 0.3s (600x faster)
- System stability increased from 70% to 95%

### Fixed
- Reactor execution rate from 0% to 54%
- Playbook matching and auto-remediation
- Circuit breaker for repeated failures

## [0.4.0] - 2026-02-22

### Added
- Plugin registry with auto-discovery
- Dashboard v1.0 with WebSocket real-time updates
- Alert management (acknowledge/resolve)
- Manual pipeline/queue triggers

## [0.3.1] - 2026-02-22

### Added
- Weekly trend analysis with sparkline charts
- Memory gap detection and repair suggestions
- Deadloop breaker with auto-circuit breaking
- Enhanced alert rules v2

## [0.3.0] - 2026-02-20

### Added
- Event bus (pub/sub + file queue)
- Sensors: FileWatcher, ProcessMonitor, SystemHealth, NetworkProbe
- Dispatcher with action suggestions
- Cooldown mechanism for sensor polling

## [0.2.0] - 2026-02-19

### Added
- 5-layer event architecture (KERNEL/COMMS/TOOL/MEM/SEC)
- Unified `emit()` event emitter
- Layer-specific convenience methods
- Backward compatibility with v0.1

## [0.1.0] - 2026-02-18

### Added
- Initial release
- Event stream (events.jsonl)
- Learning layer (lessons.md, suggestions.json)
- Analysis and reporting scripts
- ARAM plugin integration

---

## Upgrade Guide

### From 0.4.x to 0.5.0
- Install via pip: `pip install aios-framework`
- Update imports: `from aios import AIOS` instead of direct module imports
- CLI commands now use `aios` prefix: `aios health` instead of `python -m aios health`

### From 0.3.x to 0.4.0
- No breaking changes
- New plugin system is opt-in

### From 0.2.x to 0.3.0
- Event bus is backward compatible
- Sensors run automatically in pipeline

### From 0.1.x to 0.2.0
- `log_event()` API unchanged
- New layer parameter is optional (defaults to KERNEL)

---

## Roadmap

### v0.6.0 (Q2 2026)
- [ ] Integration tests
- [ ] Docker image
- [ ] Quick start guide
- [ ] API documentation

### v0.7.0 (Q3 2026)
- [ ] Plugin marketplace
- [ ] Web UI for configuration
- [ ] Cloud deployment templates

### v1.0.0 (Q4 2026)
- [ ] Production-ready release
- [ ] Full documentation
- [ ] Community contributions
- [ ] Enterprise support (optional)

---

[0.5.0]: https://github.com/yangfei222666-9/aios/releases/tag/v0.5.0
[0.4.0]: https://github.com/yangfei222666-9/aios/releases/tag/v0.4.0
[0.3.1]: https://github.com/yangfei222666-9/aios/releases/tag/v0.3.1
[0.3.0]: https://github.com/yangfei222666-9/aios/releases/tag/v0.3.0
[0.2.0]: https://github.com/yangfei222666-9/aios/releases/tag/v0.2.0
[0.1.0]: https://github.com/yangfei222666-9/aios/releases/tag/v0.1.0
