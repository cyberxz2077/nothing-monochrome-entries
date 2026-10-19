# Mechanism, evidence and checks

## Why this entry is different from an icon shortcut

This APK has an ordinary `MAIN` + `LAUNCHER` Activity and its own adaptive icon. The user adds that app entry to the home screen. It forwards an explicit intent to the original app and calls `finish()`; no service is kept alive. USB debugging is not the tinting mechanism and is unnecessary after deployment.

Many icon-customization apps instead publish pinned shortcuts with `ShortcutManager.requestPinShortcut`. A launcher may badge those with the shortcut owner's app icon. AOSP Launcher3 explicitly attaches `getShortcutInfoBadge(...)` through `withBadgeInfo(...)`. Our ordinary app entry does not take that shortcut-owner badge path. This is not a universal “no badges” guarantee: notification dots and work-profile indicators are different features, and OEM behavior may vary. A small dot cannot be identified conclusively without seeing the tool/icon involved.

Tradeoffs: a separate installed package and app-drawer entry; original app stays installed; original notifications/counts, app-info actions, dynamic icons and long-press shortcuts are not automatically inherited. Some launchers/widgets can offer other no-badge customizations; this is not claimed as a unique invention.

## What makes theme switching work

Android exposes an adaptive icon's `monochrome` layer to a supporting themed-icon launcher. Native Nothing mode colors that layer and updates with its own theme handling. The entry itself never listens for configuration changes or writes theme settings.

In the originating device session, a conventional icon pack with default/night PNGs loaded the correct variant after pack reselection but failed to update automatically on every theme change. An independent monochrome entry, with native Nothing mode selected, was accepted by the user as working. Choosing the earlier custom pack prevented this native path. This explains the design decision; it does not establish that all third-party packs or all Nothing releases behave identically.

## Evidence scope

- Originating device checked on 2026-10-19: model identifier A015, Android 16, Nothing OS **4.1** (`B4.1-260928-1140`), Nothing Launcher 4.0.20. Older handoff notes referred to an earlier OS/launcher baseline; do not reuse that as current state.
- The user confirmed the native-entry route worked. Four personal entries were built/installed and iterated with stable signing. Installed hashes and component mappings were verified. This is not a claim that every click-through and both theme directions were independently exercised for all four apps.
- The public helper uses the same Activity/monochrome mechanism but official Android signing tools and a generalized PNG pipeline. Its own build/extraction tests are reported in the repository validation note.
- Minimum API 33 is a build requirement, not proof of testing on Android 13–15. Other devices, launcher versions and desktop operating systems need validation.

## Proportional validation

1. **Before installation:** read the generated Manifest and compiled icon; verify unique independent package, original target, zero permissions/Services/Receivers, signature and stable certificate. Check foreground alpha, scale and clipping. A successful build is not proof of actual tint refresh.
2. **After installation:** compare device APK hash and resolve its launcher Activity. The helper does these checks; successful resolution is not a click-through test.
3. **Manual phone acceptance:** select native Nothing themed icons, find the extra entry, place it where desired, tap it and confirm the original app. Switch light→dark and dark→light without reselecting a pack. Confirm the symbol changes with the native icons. Avoid opening sensitive app functions during automation.
4. **When tests are already done:** reuse relevant evidence. Repeat only what changed or is still uncertain. Do not restart the failed third-party-pack investigation for every icon.
5. **Failure diagnosis:** wrong selected pack → native mode; opaque square → wrong alpha/luminance input; clipped shape → fitting; bad target → re-resolve current alias; signature mismatch → restore key; unsupported native tint → record launcher/version and stop promising theme support. Never clear the launcher database as a routine fix.

After the user accepts the result they can disconnect USB and turn off debugging. Uninstalling only the generated entry removes that entry, not the original app; get approval before cleanup and explain that its desktop placement will be lost.

## Primary sources

- [Android adaptive icons and themed monochrome layers](https://developer.android.com/develop/ui/compose/system/icon_design_adaptive)
- [Android pinned shortcuts](https://developer.android.com/develop/ui/compose/system/shortcuts/creating-shortcuts)
- [AOSP Launcher3 shortcut badging](https://android.googlesource.com/platform/packages/apps/Launcher3/+/cc1dad0cae1547c3aad40af8676d9e5312e4564b/src/com/android/launcher3/icons/IconCache.java)
- [AAPT2](https://developer.android.com/tools/aapt2), [D8](https://developer.android.com/tools/d8), [apksigner](https://developer.android.com/tools/apksigner)
