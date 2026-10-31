# Repository context used to prepare this kit

Checked `Protonk/hazy` at commit `3ea04a7ee97148b3921a3a968f3fa86d0831e27d` while preparing the kit on 2026-10-29 (America/Los_Angeles).

Read the local checkout's current guidance before using this snapshot.

- [Root guidance](https://github.com/Protonk/hazy/blob/3ea04a7ee97148b3921a3a968f3fa86d0831e27d/AGENTS.md)
- [Root README](https://github.com/Protonk/hazy/blob/3ea04a7ee97148b3921a3a968f3fa86d0831e27d/README.md)
- [Shared fixture schema](https://github.com/Protonk/hazy/blob/3ea04a7ee97148b3921a3a968f3fa86d0831e27d/Fixtures/README.md)
- [Existing derivative fixture](https://github.com/Protonk/hazy/blob/3ea04a7ee97148b3921a3a968f3fa86d0831e27d/Fixtures/hazy-derivatives-v1/README.md)
- [Fixture checker](https://github.com/Protonk/hazy/blob/3ea04a7ee97148b3921a3a968f3fa86d0831e27d/Experiments/AppleVisionTranslation/Tools/fixtures.py)

The current asset checker expects flat `images/` and `sources/`, even though Git ignore rules also cover nested assets. Keep intermediate image artifacts in `previews/`, whose contents are not included in the primary-input inventory. The current derivative smoke/medium selections use legacy transformation names; this kit's build specification accounts for that without requiring checker changes.

No source images or alterations were added to the repository while preparing this kit. The included files are a portable handoff to the local agent.

The kit was subsequently updated with the six user-supplied `v06` generations and the description prompts already delivered in this conversation. This update did not re-query or modify the Hazy repository.
