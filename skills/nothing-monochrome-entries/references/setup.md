# Setup and commands

## Device first

1. Open phone Settings → About phone and locate Build number (menu names vary). Tap it seven times and authenticate if asked. This exposes Developer options.
2. Enable **USB debugging**, not OEM unlocking. Connect a data-capable USB cable.
3. Unlock the phone and accept the RSA prompt for your trusted computer.
4. Run `adb devices -l`. Continue only when the intended device says `device`. For `unauthorized`, approve the phone prompt; for `offline`, reconnect/restart the local ADB connection; for no device, check cable/port/drivers. On Windows an OEM USB driver may be necessary. Linux may need distribution-specific udev/plugdev setup. Do not change these automatically without need.
5. Record the selected serial locally. Never publish it or an unredacted full device inventory.

Official guides: [Developer options](https://developer.android.com/studio/debug/dev-options), [hardware devices](https://developer.android.com/studio/run/device), [Platform Tools](https://developer.android.com/tools/releases/platform-tools).

## Computer tools

- Python 3.10+ and Pillow (`python -m pip install -r requirements.txt` from the repository).
- JDK 17; use an existing installation or an official distribution such as [Temurin](https://adoptium.net/temurin/releases/?version=17).
- Android SDK Platform Tools, Platform 36 and Build Tools 36.0.0. Install through Android Studio's SDK Manager or official command-line tools. The SDK manager command is `sdkmanager "platform-tools" "platforms;android-36" "build-tools;36.0.0"`; review any license terms yourself.
- Set `JAVA_HOME` to the JDK root and `ANDROID_HOME` to the SDK root, or pass `--java-home` and `--sdk`. Do not repurpose HOME/CODEX_HOME.

Expected layout: `SDK/build-tools/36.0.0/{aapt2,zipalign,lib/d8.jar,lib/apksigner.jar}` and `SDK/platforms/android-36/android.jar`. The script supports `.exe` names; macOS was exercised, Windows/Linux still need platform testing.

Commands below assume a POSIX shell and `TOOL=skills/nothing-monochrome-entries/scripts/icons.py` from the repository root. PowerShell users can call the Python path directly and pass explicit tool paths.

## Identify and extract

```sh
TOOL=skills/nothing-monochrome-entries/scripts/icons.py
python "$TOOL" doctor --adb "$ANDROID_HOME/platform-tools/adb"
# Find only the requested app, then resolve its launcher component:
adb -s SERIAL shell pm list packages
adb -s SERIAL shell cmd package query-activities --brief -a android.intent.action.MAIN -c android.intent.category.LAUNCHER APP_PACKAGE
python "$TOOL" extract APP_PACKAGE --serial SERIAL \
  --aapt2 "$ANDROID_HOME/build-tools/36.0.0/aapt2" --out work/extracted-app
```

The output directory must be new. `extraction.json` records the resolved component, APK hashes, raster candidates, direct adaptive foreground images and XML trees. `preferred_reference` is the highest-density **declared** raster candidate, not a guarantee that it matches a current dynamic/server-configured icon. Inspect it visually. When no full raster icon exists, a direct adaptive foreground image can be exported automatically; it is labeled as a layer, not a fully composed icon. For vectors or nested XML that the helper cannot render, use the XML tree to investigate or obtain a screenshot. Do not guess a random PNG from the APK and call it the launcher icon. Extracted APKs are local inspection inputs, not redistributable source assets.

## Local config

Keep the config and artwork under an ignored `work/` directory. Example (replace the component with the device's actual output):

```json
{
  "slug": "myapp",
  "label": "My App · Entry",
  "target_package": "com.example.app",
  "target_activity": "com.example.app.MainActivity",
  "version_code": 1,
  "artwork": "myapp-redrawn.png",
  "input_mode": "luminance",
  "content_dp": 60,
  "scale_percent": 100,
  "offset_dp": [0, 0]
}
```

`artwork` is relative to the config file. `luminance` expects a white symbol on black; `alpha` uses actual transparency from a cutout. The foreground is compiled as white+alpha, so output color comes from the launcher. The builder removes near-black noise (≤8/255), crops to the visible silhouette (≥32/255), fits the longest side to `content_dp × scale_percent/100`, and positions it on a 108 dp canvas rendered at 432 pixels. This normalization differs from scaling an entire source image with arbitrary margins. Record a baseline before iterating.

## Sign, build, install

```sh
python "$TOOL" init-key --signing-dir .local/signing
python "$TOOL" build --config work/myapp.json --signing-dir .local/signing --out out
# Use the exact APK path printed by build:
python "$TOOL" install --serial SERIAL --apk out/local.monochrome.entry.myapp/VERSION-HASH/entry.apk
```

`init-key` refuses an existing directory. Back up the whole signing folder privately: PKCS12 key, password and certificate pin. Never commit them. Losing the key prevents same-package updates; restoring the backup is preferable to uninstalling an entry and losing its placement.

`build` is local only. `install` is the only helper command that writes to the phone. It installs one independent package, verifies its signature/package/permissions before installation and checks its on-device SHA-256 afterward. It does not launch the target app, change themes, remove icons or uninstall anything. An explicit install command is not a replacement for the agent checking user authorization.

For updates, retain `slug` and signing folder, increase `version_code`, change only requested artwork/geometry and use `install` again. Original app data remains owned by its original package. If a target app updates its launch alias, re-resolve the component and rebuild the entry.
