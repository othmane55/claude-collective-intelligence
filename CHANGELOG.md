# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Professional documentation structure with categorized folders
- CONTRIBUTING.md for contributor guidelines
- SECURITY.md for security policy
- CHANGELOG.md for version tracking
- `docs/lessons/LESSONS_LEARNED.md` - Critical architectural lessons documentation

### Changed
- Reorganized 97 markdown files from root to `docs/` subdirectories
- Documentation now follows industry-standard categorization

### Fixed
- Security vulnerability in `jws` package (npm audit fix)
- LICENSE consistency (Apache 2.0 across all files)

### Identified (Pending Implementation)
- **Result Queue Architecture Conflict** (December 7, 2025)
  - Single `agent.results` queue used for dual purposes causes race condition
  - Workers and Leaders compete for same messages
  - Proposed Solution: Separate `agent.brainstorm.results` queue
  - See: `docs/lessons/LESSONS_LEARNED.md` for full analysis

## [1.0.0] - 2024-12-04

### Added
- Multi-agent orchestration system with RabbitMQ
- Event-driven architecture with CQRS pattern
- PostgreSQL persistence layer with migrations
- Redis caching integration
- Comprehensive monitoring with Prometheus/Grafana
- Docker and Docker Compose deployment
- CI/CD pipeline with GitHub Actions
- Unit, integration, and E2E test suites
- API documentation with OpenAPI/Swagger
- SDK for TypeScript/JavaScript clients
- Brainstorming and voting system for agents
- Mentorship system for agent training
- Career progression tracking
- Performance metrics and dashboards

### Infrastructure
- RabbitMQ 3.12+ message broker
- PostgreSQL 15+ database
- Redis 7+ caching
- OpenTelemetry instrumentation
- Structured logging system

### Documentation
- Architecture documentation
- API reference
- Deployment guides
- Troubleshooting guides
- Performance tuning guides

---

## Version History Summary

| Version | Date       | Highlights                           |
|---------|------------|--------------------------------------|
| 1.0.0   | 2024-12-04 | Initial release with full feature set |

[Unreleased]: https://github.com/umitkacar/plugin-ai-agent-rabbitmq/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/umitkacar/plugin-ai-agent-rabbitmq/releases/tag/v1.0.0
