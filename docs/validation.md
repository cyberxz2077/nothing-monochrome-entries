# Validation record — 2026-10-19

The reusable tool was separated from an existing personal prototype. Vendor APKs, brand artwork, signing material, device identifiers and screenshots are not part of this repository.

## Public helper

- Six Python unit tests passed: launcher alias expansion, separate package identity, unsafe component rejection, self-target/invalid-version rejection, alpha-mask behavior/source preservation, opaque-alpha rejection, and clipping/empty-symbol failures (some tests cover more than one invariant).
- The Codex skill frontmatter/structure validator passed.
- A real adaptive-icon app was inspected through authorized USB ADB on macOS. The helper pulled its APK, resolved its launcher component, followed the adaptive foreground reference and extracted five density variants, including the 432×432 source foreground. That result was visually inspected. This is a foreground layer, not a claim of fully composing all adaptive icons.
- A generic independent entry was compiled using Temurin JDK 17, Android API 36, Build Tools 36.0.0, AAPT2, D8, zipalign and apksigner. `apksigner verify` passed and the certificate matched the persistent local identity.
- An independent resource/DEX reader checked the resulting package, absence of permissions/Services/Receivers, the compiled `monochrome` reference, and the original application's target component.
- The geometry check rejected an overlarge draft before build output; reducing the explicit content size produced a valid foreground.

The generalized helper's new test entry was **not installed** as another duplicate on the phone. Its explicit `install` subcommand therefore still needs direct end-to-end validation with this generalized build. Its install/hash-verification sequence is the same approach used successfully by the originating prototype. Do not report that as a fresh installation test of this helper.

## Original device experience

The earlier prototype supplied independent native monochrome entries for four selected apps. Installation, component mapping, signatures and on-device APK hashes were checked; the user confirmed the native-entry route worked and iterated artwork/scale on the phone. That acceptance is not a full automated matrix of every app, action, launcher, mask and theme transition.

Current device environment read on 2026-10-19: model identifier A015, Android 16, Nothing OS 4.1 (`B4.1-260928-1140`), Nothing Launcher 4.0.20. The minimum SDK 33 declaration does not imply Android 13–15 testing. Windows/Linux paths are implemented but have not been exercised here.

## Repeat locally

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Then follow the setup reference to build from your own approved icon. Verify the installed hash, actual click-through, selected native Nothing mode and both light/dark directions on your own device. Avoid repeating unrelated experiments when those conditions have already been verified and nothing relevant changed.
