# Changelog

## [0.1.2](https://github.com/roquerodrigo/xiaomi-vacuum-sdk/compare/v0.1.1...v0.1.2) (2026-11-08)

This release adds support for maps from Dreame-built Xiaomi-brand vacuums, including their rooms, and moves release automation to Release Autopilot.

### New features

- Maps from Dreame-built vacuums sold under the Xiaomi brand, such as the X20+, can now be decoded and rendered, including the named rooms. ([#14](https://github.com/roquerodrigo/xiaomi-vacuum-sdk/pull/14))
- Parsed maps now list their rooms, including unnamed ones, so consumers can offer room-based cleaning for these models. ([#14](https://github.com/roquerodrigo/xiaomi-vacuum-sdk/pull/14))

### Improvements

- Release notes and versioning are now handled by Release Autopilot, which keeps the release pull request up to date. ([#13](https://github.com/roquerodrigo/xiaomi-vacuum-sdk/pull/13))

## [0.1.1](https://github.com/roquerodrigo/xiaomi-vacuum-sdk/compare/v0.1.0...v0.1.1) (2026-09-21)


### Features

* **map:** return the render geometry alongside the PNG ([f5bb8b9](https://github.com/roquerodrigo/xiaomi-vacuum-sdk/commit/f5bb8b96b6358d9081ec3dbcb3ad8a2259be05f1))


### Code Refactoring

* **map:** return a map point from the pixel projection ([678325f](https://github.com/roquerodrigo/xiaomi-vacuum-sdk/commit/678325f9d24257b311405f267e29010894c827b1))


### Documentation

* add GitHub Sponsors button and support section ([7ec0871](https://github.com/roquerodrigo/xiaomi-vacuum-sdk/commit/7ec08719881d51e2511597e268ff0dc6d59d5e1e))
* point at the inlined map fixtures ([8356d30](https://github.com/roquerodrigo/xiaomi-vacuum-sdk/commit/8356d303b7b8c2d91a0441a847cdd0d030c08d8f))

## 0.1.0 (2026-08-09)


### Features

* **map:** add map blob decryption, parsing and PNG rendering ([0946d93](https://github.com/roquerodrigo/xiaomi-vacuum-sdk/commit/0946d93f7d9177728d04262589465a5cd48524b4))
* **map:** pad the rendered map with a configurable border ([383aa35](https://github.com/roquerodrigo/xiaomi-vacuum-sdk/commit/383aa35cff01d8d92aa8d023f1420d16a87fcfd7))
* **miot:** add async MIoT local-control client ([5eed29e](https://github.com/roquerodrigo/xiaomi-vacuum-sdk/commit/5eed29eb34e90adf06698f4cf8bb5e3c21d15d9c))


### Bug Fixes

* **miot:** match property rows by siid/piid instead of did ([e15d956](https://github.com/roquerodrigo/xiaomi-vacuum-sdk/commit/e15d95650296bc96ae1386eaffe706c26ed9e44e))


### Miscellaneous Chores

* scaffold SDK repository ([45a5e1c](https://github.com/roquerodrigo/xiaomi-vacuum-sdk/commit/45a5e1c2e9ceb4c3c78e5ba744ee64bdbf7d6271))
