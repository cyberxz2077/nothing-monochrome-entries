# Nothing Monochrome Entries

[简体中文](README.zh-CN.md)

Redraw a few app icons that look out of place on Nothing OS, while keeping the rest of your icons in their usual Nothing style. This repository provides a reusable AI-agent skill and local tools for extracting icons, building entries and installing them over USB.

Each replacement is a **small, independently installed app with a custom icon**. Tap it to open the original app. Nothing Launcher handles its light/dark colours. The original app and official Nothing pack stay unchanged.

**USB is only needed for setup.** After installation, you can unplug the phone and turn off USB debugging. The entries need no root, Accessibility service, extra app permissions or background service. This is an independent project, unaffiliated with Nothing.

## How the icons follow your theme

Android's adaptive icons can contain two kinds of artwork with different jobs.

- **Foreground and background layers** let the launcher fit a colour icon into shapes such as circles or rounded squares.
- An optional **single-colour layer**, called `monochrome`, gives a supporting launcher a shape it can recolour to match the theme.

An app can support the first two layers without supplying the single-colour version. Some systems also generate themed icons automatically, but conversion can leave cluttered details or awkward proportions. Missing this optional layer does not by itself mean the app breaks Android's basic icon rules. See [Android's adaptive icon documentation](https://developer.android.com/develop/ui/compose/system/icon_design_adaptive).

Our entry supplies a deliberately redrawn single-colour shape. With **native Nothing themed icons selected**, the launcher colours it and handles theme changes. The entry does not watch for theme switches or run a background listener. A separately selected icon pack can bypass this native path; the [mechanism notes](skills/nothing-monochrome-entries/references/validation.md) describe the earlier pack experiment that led to this approach.

## What happens when you tap an entry

The entry asks Android to open the original app's launch component, then immediately ends its own Activity. It uses Android's [`Theme.NoDisplay`](https://developer.android.com/reference/android/R.style#Theme_NoDisplay), so it has no screen of its own to show in between. It also stays out of recent apps and the back stack.

On the original test phone, this avoided an extra page or flash during launch. The original app's loading screen and the system's normal animations can still appear; forwarding does not remove the app's startup time. The implementation is in [MainActivity.java](skills/nothing-monochrome-entries/assets/MainActivity.java).

## How this differs from an icon shortcut

Many icon-customization tools create **pinned shortcuts**. The launcher may put a small badge on them to identify the app that created the shortcut. These entries are ordinary installed apps, so they do not use that shortcut-owner badge mechanism. [AOSP Launcher3 shows this distinction in its shortcut handling](https://android.googlesource.com/platform/packages/apps/Launcher3/+/cc1dad0cae1547c3aad40af8676d9e5312e4564b/src/com/android/launcher3/icons/IconCache.java).

The tradeoff is an extra app in your app drawer. The original app stays installed, and its notification dots/counts, long-press shortcuts, dynamic icons and app-info actions do not transfer to the entry. Work-profile badges are a separate feature and may still appear.

## Get started with an AI agent

Clone this repository and copy `skills/nothing-monochrome-entries` into your agent's skill directory. For Codex, that is usually `~/.codex/skills/`. Check and merge any existing same-name skill before replacing files.

Then ask your agent something like this.

> Use $nothing-monochrome-entries to redraw the icons for these apps and create entries that follow Nothing's light/dark theme. Keep my other icons as they are. Start by checking the USB connection and extracting the original icons.

The workflow is as follows.

1. Enable **Developer options**, then **USB debugging**. Connect a data-capable cable, unlock the phone and authorize your computer. Confirm that `adb devices -l` reports `device`.
2. Let the agent identify the selected app and its actual launch component, then extract its icon over USB. The helper supports declared raster images and directly referenced adaptive foregrounds; use a screenshot when vector or nested resources cannot be rendered.
3. Redraw the symbol with an available image tool, or supply your own artwork. Keep recognizable features, simplify small details, and adjust stroke weight, spacing and size against the existing Nothing icons. Review the sample before installation.
4. Build and sign a separate entry with the official Android tools, keeping the signing key for future updates.
5. Install the entry, keep native Nothing themed icons selected, and place the new icon on your home screen. Check that it opens the right app and changes in both light-to-dark and dark-to-light directions without reselecting an icon pack.

The agent needs local file and command access; redrawing needs an image tool. You approve the USB connection and the artwork. The [setup guide](skills/nothing-monochrome-entries/references/setup.md) covers the tools and commands; [redrawing guidelines](skills/nothing-monochrome-entries/references/artwork.md) cover the artwork.

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

Keep `.local/signing` private and backed up. For updates, retain the entry's package name and signing key, then increase its version code. If the original app changes its launch component, resolve it again and rebuild the entry.

## Tested scope

The original prototype was used on a **CMF Phone 1 (A015), Android 16, Nothing OS 4.1 and Nothing Launcher 4.0.20**. Four entries were installed and their artwork refined with the user's phone feedback. The user accepted the native theme behaviour and launch experience.

The reusable public helper passed unit tests, real icon extraction, build/signature checks and compiled resource checks on macOS. Its newly generated test entry was **not installed on the phone**, so the public helper's install command still needs its own end-to-end test. Other phones, launcher versions, Windows and Linux also need testing; minimum SDK 33 is not evidence of Android 13–15 compatibility testing.

See the [validation record](docs/validation.md) for the exact scope and the [phone acceptance checks](skills/nothing-monochrome-entries/references/validation.md) for your own setup. Run local tests with `python -m unittest discover -s tests -v`.

## License and contents

This repository distributes source and instructions. Signing keys, passwords, extracted APKs, private configs and generated builds stay local and are excluded from Git. It does not distribute vendor APKs, brand icon collections or ready-made signed entries.

MIT-licensed code and documentation. Third-party app names and artwork remain their owners' property; the license does not grant rights to those marks. Development and documentation were AI-assisted, with the design direction and phone feedback supplied by the user.
