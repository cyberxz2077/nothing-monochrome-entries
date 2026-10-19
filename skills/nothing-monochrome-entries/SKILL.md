---
name: nothing-monochrome-entries
description: Redraw missing Nothing-style app icons and build independent Android launcher entries with native monochrome theming. Use for a few unsupported apps on Nothing Launcher while preserving other apps' native style, including USB setup, icon extraction, artwork iteration, signing and installation. Not for modifying the official icon pack or replacing original apps.
license: MIT
---

# Nothing monochrome entries

Create a tiny installed app for each target. Its adaptive icon supplies a `monochrome` layer; its visible launcher Activity opens the original app and immediately finishes. Native Nothing Launcher owns tint and theme refresh. USB/ADB is a setup and deployment channel, not a runtime dependency.

## Establish the working scope

- Identify the selected apps, preferred labels and requested visual changes. Reuse approved artwork and previously verified behavior.
- Explain the tradeoff once: this adds an independent app entry; the original app remains installed. Its notification dots, long-press app shortcuts and app-info page are not inherited. Theme support depends on the launcher and selected native mode.
- Keep package IDs and signing identity stable between updates. Do not re-sign the original app, replace Nothing packages, request root, use a third-party icon pack, or add a background service to solve theme refresh.

## Connect and identify

Read [setup.md](references/setup.md) for USB and toolchain setup. Order matters: enable Developer options → enable USB debugging → connect a data cable → unlock and accept the computer's RSA prompt → verify `adb devices -l` reports `device`.

Use `scripts/icons.py doctor`; explicitly select the intended serial for device commands. `unauthorized`, `offline`, no device, and multiple devices are distinct conditions. Let the user handle authentication; do not enable OEM unlocking or change the bootloader.

Resolve the app's current MAIN/LAUNCHER component from the device, including an activity-alias where applicable. Do not infer a package or Activity from its label. With multiple launchable entries, show the relevant candidates and use the intended one.

Use `extract` to pull only the selected app's APK/splits and extract declared raster icon candidates. Inspect the reported reference before redrawing. For adaptive icons with a direct PNG/WebP foreground, the helper also follows that declared resource across APK splits and exports the foreground as a clearly labeled reference. It preserves XML trees but does not compose complex vectors/nested layers; use a suitable local Android drawable renderer or ask for a clean screenshot/original. Do not use APKs, private device logs or serials as public assets.

## Redraw and review

Read [artwork.md](references/artwork.md). Use an available image-generation/editing tool for raster redraws; use native vector tools for editable vector sources. Preserve brand recognition and user-selected features. Explain only the meaningful visual change, show a small preview, and iterate from the user's corrections. If artwork is already approved, reuse it without another design round.

Separate shape changes from scaling. Interpret “110%” as width and height relative to an explicitly recorded baseline, not relative to the previous iteration. Scale only the foreground. Keep system background tint and mask under launcher control. Evaluate both light and dark contrast and the actual small-icon silhouette; the builder checks a circular mask and reports departures from Android's conservative safe square.

## Build and install

Use the commands and config schema in [setup.md](references/setup.md). The script uses official AAPT2, D8, zipalign and apksigner, JDK 17 and Pillow. It never downloads tools, accepts SDK licenses, installs software, or changes device settings implicitly.

1. Create one persistent private signing identity using `init-key`; keep a private backup. A partial/mismatched identity is a stop condition, not permission to regenerate it.
2. Set exact target component, descriptive entry label, artwork mode and baseline geometry in a local config. `local.monochrome.entry.<slug>` is distinct from the original package. Increment `version_code` for an update.
3. Build; inspect the PNG foreground, Manifest, signature verification and `build.json`. No permissions, Service, Receiver, shortcut API, analytics or network code should exist. Only the launcher Activity is exported.
4. Install when the user has authorized installation within this task. Explicit `install` uses `adb install -r` and verifies the installed APK hash. A signature mismatch is not a reason to uninstall or erase data automatically.
5. Ask the user to choose the **native Nothing icon mode** and put the new entry on the home screen. Do not silently change settings or move existing icons. An earlier custom icon pack may prevent native monochrome tinting.

## Verify and report

Read [validation.md](references/validation.md). Verify build, installed identity, click-through, and both light→dark and dark→light behavior at the scope the user authorized. When the user prefers testing themselves, install and report the remaining manual checks. Never label a local preview as a device screenshot or infer successful app launch from component resolution.

Do not repeat completed third-party-pack compatibility experiments. In the original device test, day/night PNG variants changed only after reselecting the pack; adding more variants did not fix automatic refresh. The native-entry path avoids this by giving the launcher its own monochrome layer.

Return the entry name, what changed, where the source/config/APK live, which checks passed, and what remains untested. After setup, the user can unplug the cable and disable USB debugging; normal icon operation does not need a computer or resident helper. Keep originals, prior artwork and signed builds until the user chooses cleanup.
