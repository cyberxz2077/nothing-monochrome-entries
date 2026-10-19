# Nothing Monochrome Entries

[简体中文](README.zh-CN.md)

An AI-agent skill and local build tool for filling a few missing Nothing-style app icons while keeping the rest of the home screen in native Nothing mode.

Each custom icon is a **small, independent Android launcher app**. Its adaptive icon contains a `monochrome` layer. Tapping it opens the original app and immediately finishes the entry Activity. Nothing Launcher handles the icon's tint and light/dark changes.

**USB debugging is used to inspect apps and install entries. It is not needed afterward.** No root, Accessibility service, background listener, network permission, official-pack modification or replacement of the original app is involved. This project is independent of Nothing.

## What the workflow does

1. Help enable Developer options and USB debugging, connect a data cable, and authorize the computer.
2. Find the actual app package and launcher Activity/alias.
3. Extract a declared raster icon or direct adaptive foreground from the installed APK/splits. Fall back to a user screenshot for unsupported nested/vector resources.
4. Use an available AI image editor—or user-supplied artwork—to simplify and refine the symbol. Keep recognizable features, open counters, usable stroke weight and a recorded scale baseline.
5. Compile and sign an independent entry with official Android tools; preserve the signing identity for later updates.
6. Install, choose the native Nothing icon mode, and test click-through plus both theme directions.

This is a guided workflow, not a promise that connecting any AI automatically completes every device setup. The agent needs local command/file access; raster redraws need a suitable image tool. USB authorization and visual acceptance remain user actions.

## Use as a skill

Clone this repository, then copy `skills/nothing-monochrome-entries` into your agent's skill directory. For Codex, the usual location is `~/.codex/skills/`. Inspect an existing same-name skill before merging; do not overwrite it blindly.

Example request:

> Use $nothing-monochrome-entries to redraw the unsupported icons for these apps and create native themed launcher entries. Keep my other Nothing icons as they are. Start by checking my USB connection and extracting the original icons.

The skill includes [USB/toolchain setup and exact commands](skills/nothing-monochrome-entries/references/setup.md), [redrawing guidelines](skills/nothing-monochrome-entries/references/artwork.md), and [verification, mechanism and limitations](skills/nothing-monochrome-entries/references/validation.md).

## Use the scripts directly

Requires Python 3.10+, Pillow, JDK 17, Android Platform 36 and Build Tools 36.0.0. Follow the setup reference before these commands; existing SDK/JDK installations can be reused.

```sh
python -m pip install -r requirements.txt
TOOL=skills/nothing-monochrome-entries/scripts/icons.py
python "$TOOL" --help
python "$TOOL" doctor
python "$TOOL" init-key --signing-dir .local/signing
python "$TOOL" build --config work/myapp.json --signing-dir .local/signing --out out
```

Set `JAVA_HOME` and `ANDROID_HOME`, or use explicit flags. See the setup reference for the config schema and the explicit `extract` / `install` commands. Building never installs; installing never switches themes or opens the original app.

Keep `.local/signing` private and backed up. Keys, passwords, pulled APKs, private configs and generated builds are excluded from Git. This repository distributes source and instructions, not brand icon collections, vendor APKs or ready-made signed entries.

## Why there is no shortcut-owner badge

Many custom-icon tools create **pinned shortcuts**, which launchers can mark with the publishing app's badge. This project creates a normal installed app's launcher Activity, so that shortcut-owner badging path does not apply. Notification dots and work-profile badges are separate; it is not a guarantee that every launcher will show no indicators. See the [AOSP implementation](https://android.googlesource.com/platform/packages/apps/Launcher3/+/cc1dad0cae1547c3aad40af8676d9e5312e4564b/src/com/android/launcher3/icons/IconCache.java).

## Tradeoffs and tested scope

- The entry is a separate app; the original remains in the app drawer. Original notification counts, app-info actions, dynamic icons and long-press shortcuts do not transfer automatically.
- Select **native Nothing themed icons**. A custom icon pack may bypass the native monochrome path.
- Same package + same key + higher version permits updating the entry without deliberately replacing its launcher component. Back up the key.
- The originating user accepted the native-entry route on A015 / Android 16 / Nothing OS 4.1 / Nothing Launcher 4.0.20. This is not a universal compatibility claim. Other versions and launchers need testing.
- USB debugging can be disabled after installation. The entry does not maintain a background process or depend on the computer.

Read the [validation record](docs/validation.md) for what was actually checked. Run local tests with `python -m unittest discover -s tests -v`.

MIT-licensed code and documentation. Third-party app names and artwork remain their owners' property; the license does not grant rights to those marks. Development and documentation were AI-assisted, with the design direction and phone feedback supplied by the user.
