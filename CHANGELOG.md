# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

<!-- Add new changes here -->

## [0.1.0] - 2025-09-15

### Added

- Added /health endpoint.
- Added /upload endpoint.
- Implemented configurable upload size limiting (UPLOAD_MAX_BYTES, default 10MB).
- Implemented in-memory rate limiting for /upload and /health with headers (X-RateLimit-*).
- Added GitHub Actions CI workflow running pytest on Python 3.11 & 3.12.
- Updated README with Operational Hardening section and CI badge.