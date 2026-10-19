#!/usr/bin/env python3
"""Build normal Android launcher entries with native monochrome icons.

Device writes occur only in the explicit install command. No root, background
service, shortcut API, launcher database access, or theme settings writes.
"""
from pathlib import Path
import argparse
import hashlib
import io
import json
import math
import os
import re
import secrets
import shlex
import shutil
import subprocess
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET

ASSETS = Path(__file__).resolve().parent.parent / 'assets'
ANDROID = '{http://schemas.android.com/apk/res/android}'
PACKAGE = re.compile(r'[a-zA-Z][a-zA-Z0-9_]*(?:\.[a-zA-Z][a-zA-Z0-9_]*)+')
ACTIVITY = re.compile(r'[a-zA-Z][a-zA-Z0-9_]*(?:\.[a-zA-Z_$][a-zA-Z0-9_$]*)+')
SLUG = re.compile(r'[a-z][a-z0-9_]{1,39}')


def run(command, *, env=None, binary=False):
    p = subprocess.run(list(map(str, command)), capture_output=True, text=not binary,
                       env=env, timeout=120)
    if p.returncode:
        error = p.stderr.decode(errors='replace') if binary else p.stderr
        raise RuntimeError(f'{Path(str(command[0])).name} failed: {error.strip()}')
    return p.stdout if binary else p.stdout.strip()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def tools(args):
    sdk = Path(args.sdk).resolve()
    jdk = Path(args.java_home).resolve()
    suffix = '.exe' if os.name == 'nt' else ''
    bt = sdk / 'build-tools' / args.build_tools
    result = {name: bt / (name + suffix) for name in ('aapt2', 'zipalign')}
    result.update({name: jdk / 'bin' / (name + suffix) for name in ('java', 'javac', 'keytool')})
    result.update(android=sdk / 'platforms' / ('android-' + str(args.api)) / 'android.jar',
                  d8=bt / 'lib/d8.jar', apksigner=bt / 'lib/apksigner.jar')
    missing = [str(p) for p in result.values() if not p.is_file()]
    if missing:
        raise ValueError('Missing official SDK/JDK files:\n' + '\n'.join(missing))
    return result


def config(path):
    path = Path(path).resolve()
    c = json.loads(path.read_text(encoding='utf-8'))
    if not SLUG.fullmatch(c['slug']):
        raise ValueError('slug must be 2–40 lowercase letters, digits or underscores')
    if not PACKAGE.fullmatch(c['target_package']):
        raise ValueError('Invalid target package')
    if c['target_activity'].startswith('.'):
        c['target_activity'] = c['target_package'] + c['target_activity']
    if not ACTIVITY.fullmatch(c['target_activity']):
        raise ValueError('Invalid target activity')
    c['entry_package'] = 'local.monochrome.entry.' + c['slug']
    if c['entry_package'] == c['target_package']:
        raise ValueError('An entry cannot target itself')
    if type(c['version_code']) is not int or not 1 <= c['version_code'] <= 2100000000:
        raise ValueError('version_code must be a positive Android version code')
    if not isinstance(c['label'], str) or not c['label'].strip() or len(c['label']) > 80:
        raise ValueError('Provide a short visible entry label')
    c['artwork'] = str((path.parent / c['artwork']).resolve())
    c.setdefault('input_mode', 'luminance')
    c.setdefault('content_dp', 60)
    c.setdefault('scale_percent', 100)
    c.setdefault('offset_dp', [0, 0])
    for name, low, high in [('content_dp', 24, 72), ('scale_percent', 50, 150)]:
        value = c[name]
        if not isinstance(value, (float, int)) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f'Invalid {name}')
    offset = c['offset_dp']
    if len(offset) != 2 or not all(isinstance(v, (float, int)) and math.isfinite(v) and abs(v) <= 12 for v in offset):
        raise ValueError('offset_dp must contain two small finite numbers')
    return c


def render(c):
    from PIL import Image, ImageChops
    with Image.open(c['artwork']) as original:
        original.load()
        source = original.convert('RGBA')
    if c['input_mode'] == 'alpha':
        alpha = source.getchannel('A')
        if alpha.getextrema() == (255, 255):
            raise ValueError('alpha mode requires actual transparency; opaque input would become a square')
    elif c['input_mode'] == 'luminance':
        alpha = ImageChops.multiply(source.convert('L'), source.getchannel('A'))
    else:
        raise ValueError('input_mode must be alpha or luminance')
    alpha = alpha.point(lambda v: 0 if v <= 8 else v)
    box = alpha.point(lambda v: 255 if v >= 32 else 0).getbbox()
    if box is None:
        raise ValueError('No visible monochrome silhouette')
    alpha = alpha.crop(box)
    span = c['content_dp'] * c['scale_percent'] / 100 * 4
    ratio = span / max(alpha.size)
    size = tuple(max(1, round(v * ratio)) for v in alpha.size)
    alpha = alpha.resize(size, Image.Resampling.LANCZOS)
    layer = Image.new('L', (432, 432), 0)
    xy = tuple(round((432 - size[i]) / 2 + c['offset_dp'][i] * 4) for i in (0, 1))
    if any(xy[i] < 0 or xy[i] + size[i] > 432 for i in (0, 1)):
        raise ValueError('Foreground would leave the canvas')
    layer.paste(alpha, xy)
    points = [(x, y) for y in range(432) for x in range(432) if layer.getpixel((x, y)) >= 32]
    radius = max(math.hypot(x - 215.5, y - 215.5) for x, y in points)
    if radius >= 144:
        raise ValueError('Visible artwork exceeds the central 72 dp circular mask; adjust size or position')
    outside_safe_square = sum(not (84 <= x < 348 and 84 <= y < 348) for x, y in points)
    icon = Image.new('RGBA', (432, 432), (255, 255, 255, 0))
    icon.putalpha(layer)
    data = io.BytesIO(); icon.save(data, 'PNG')
    return data.getvalue(), {'source_crop': box, 'visible_bounds': layer.point(lambda v: 255 if v >= 32 else 0).getbbox(),
                            'max_radius_px': round(radius, 3), 'pixels_outside_66dp_square': outside_safe_square}


def identity(args, tc, create=False):
    folder = Path(args.signing_dir).resolve()
    key, password, pin = folder / 'entry.p12', folder / 'password.txt', folder / 'certificate.sha256'
    if create:
        if folder.exists():
            raise ValueError('Signing directory already exists; never replace an existing identity')
        folder.mkdir(parents=True, mode=0o700)
        password.write_text(secrets.token_urlsafe(36), encoding='utf-8'); password.chmod(0o600)
        env = dict(os.environ, MONO_SIGNING_PASSWORD=password.read_text())
        run([tc['keytool'], '-genkeypair', '-keystore', key, '-storetype', 'PKCS12', '-alias', 'entry',
             '-keyalg', 'RSA', '-keysize', '2048', '-validity', '10000', '-dname', 'CN=Local Monochrome Entry',
             '-storepass:env', 'MONO_SIGNING_PASSWORD', '-keypass:env', 'MONO_SIGNING_PASSWORD'], env=env)
        key.chmod(0o600)
        cert = run([tc['keytool'], '-exportcert', '-keystore', key, '-alias', 'entry',
                    '-storepass:env', 'MONO_SIGNING_PASSWORD'], env=env, binary=True)
        pin.write_text(sha(cert) + '\n', encoding='utf-8')
    if not all(p.is_file() for p in (key, password, pin)):
        raise ValueError('Incomplete signing identity; run init-key in a new private directory or restore your backup')
    if os.name != 'nt' and any(p.stat().st_mode & 0o077 for p in (key, password)):
        raise ValueError('Signing key and password must be readable only by the owner (chmod 600)')
    env = dict(os.environ, MONO_SIGNING_PASSWORD=password.read_text(encoding='utf-8').strip())
    cert = run([tc['keytool'], '-exportcert', '-keystore', key, '-alias', 'entry',
                '-storepass:env', 'MONO_SIGNING_PASSWORD'], env=env, binary=True)
    if sha(cert) != pin.read_text().strip():
        raise ValueError('Signing certificate changed; refusing update')
    return key, env, sha(cert)


def build_entry(args):
    tc = tools(args); c = config(args.config)
    key, env, fingerprint = identity(args, tc)
    png, geometry = render(c)
    ET.register_namespace('android', ANDROID[1:-1])
    manifest = ET.Element('manifest', {'package': c['entry_package'], ANDROID+'versionCode': str(c['version_code']),
                                      ANDROID+'versionName': str(c['version_code'])})
    ET.SubElement(manifest, 'uses-sdk', {ANDROID+'minSdkVersion': '33', ANDROID+'targetSdkVersion': str(args.api)})
    app = ET.SubElement(manifest, 'application', {ANDROID+'label': c['label'], ANDROID+'icon': '@drawable/ic_entry',
                         ANDROID+'roundIcon': '@drawable/ic_entry', ANDROID+'allowBackup': 'false'})
    activity = ET.SubElement(app, 'activity', {ANDROID+'name': '.MainActivity', ANDROID+'exported': 'true',
                             ANDROID+'theme': '@android:style/Theme.NoDisplay', ANDROID+'noHistory': 'true',
                             ANDROID+'excludeFromRecents': 'true'})
    intent = ET.SubElement(activity, 'intent-filter')
    ET.SubElement(intent, 'action', {ANDROID+'name': 'android.intent.action.MAIN'})
    ET.SubElement(intent, 'category', {ANDROID+'name': 'android.intent.category.LAUNCHER'})
    with tempfile.TemporaryDirectory(prefix='monochrome-entry-') as tmp:
        work = Path(tmp); res = work/'res'
        for d in ('drawable-nodpi', 'drawable-anydpi-v33', 'values'): (res/d).mkdir(parents=True)
        (res/'drawable-nodpi/foreground.png').write_bytes(png)
        (res/'drawable-anydpi-v33/ic_entry.xml').write_text('<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android"><background android:drawable="@color/background"/><foreground android:drawable="@drawable/foreground"/><monochrome android:drawable="@drawable/foreground"/></adaptive-icon>')
        (res/'values/colors.xml').write_text('<resources><color name="background">#202020</color></resources>')
        mf = work/'AndroidManifest.xml'; ET.ElementTree(manifest).write(mf, encoding='utf-8', xml_declaration=True)
        main = (ASSETS/'MainActivity.java').read_text().replace('ENTRY_PACKAGE', c['entry_package'])
        (work/'MainActivity.java').write_text(main, encoding='utf-8')
        (work/'EntryTarget.java').write_text('package '+c['entry_package']+';\nfinal class EntryTarget {\n'+
            '\n'.join('static final String '+name+' = '+json.dumps(c[field])+';' for name, field in
                      [('PACKAGE','target_package'),('ACTIVITY','target_activity'),('LABEL','label')])+'\n}\n')
        run([tc['aapt2'], 'compile', '--dir', res, '-o', work/'resources.zip'])
        run([tc['aapt2'], 'link', '-o', work/'resources.apk', '-I', tc['android'], '--manifest', mf, work/'resources.zip'])
        (work/'classes').mkdir(); (work/'dex').mkdir()
        run([tc['javac'], '--release', '8', '-encoding', 'UTF-8', '-classpath', tc['android'], '-d', work/'classes',
             work/'MainActivity.java', work/'EntryTarget.java'])
        run([tc['java'], '-cp', tc['d8'], 'com.android.tools.r8.D8', '--release', '--min-api', '33',
             '--lib', tc['android'], '--output', work/'dex', *sorted((work/'classes').rglob('*.class'))])
        with zipfile.ZipFile(work/'resources.apk') as z: entries = {name: z.read(name) for name in z.namelist()}
        entries['classes.dex'] = (work/'dex/classes.dex').read_bytes()
        with zipfile.ZipFile(work/'unsigned.apk', 'w') as z:
            for name, data in sorted(entries.items()):
                z.writestr(zipfile.ZipInfo(name, (2026,1,1,0,0,0)), data)
        run([tc['zipalign'], '-p', '4', work/'unsigned.apk', work/'aligned.apk'])
        run([tc['java'], '-jar', tc['apksigner'], 'sign', '--ks', key, '--ks-key-alias', 'entry',
             '--ks-pass', 'env:MONO_SIGNING_PASSWORD', '--key-pass', 'env:MONO_SIGNING_PASSWORD',
             '--v4-signing-enabled', 'false', '--out', work/'entry.apk', work/'aligned.apk'], env=env)
        verification = run([tc['java'], '-jar', tc['apksigner'], 'verify', '--verbose', '--print-certs', work/'entry.apk'])
        if fingerprint not in verification: raise ValueError('Unexpected signed certificate')
        signed = (work/'entry.apk').read_bytes()
        metadata = {'entry_package': c['entry_package'], 'version_code': c['version_code'], 'label': c['label'],
                    'target_package': c['target_package'], 'target_activity': c['target_activity'],
                    'sha256': sha(signed), 'certificate_sha256': fingerprint, 'artwork_sha256': sha(Path(c['artwork']).read_bytes()),
                    'input_mode': c['input_mode'], 'content_dp': c['content_dp'], 'scale_percent': c['scale_percent'],
                    'offset_dp': c['offset_dp'], 'geometry': geometry, 'permissions': [], 'services': [], 'receivers': [],
                    'native_monochrome': True, 'toolchain_api': args.api, 'build_tools': args.build_tools}
        out = Path(args.out)/c['entry_package']/(str(c['version_code'])+'-'+sha(signed)[:16])
        out.mkdir(parents=True, exist_ok=False)
        (out/'entry.apk').write_bytes(signed); (out/'foreground.png').write_bytes(png)
        (out/'AndroidManifest.xml').write_bytes(mf.read_bytes()); (out/'verification.txt').write_text(verification+'\n')
        write_json(out/'build.json', metadata)
    print(out/'entry.apk')
    if geometry['pixels_outside_66dp_square']: print('Review: glyph extends outside Android’s conservative 66 dp safe square.', file=sys.stderr)


def adb(args, *words):
    if not args.serial: raise ValueError('Select one authorized device explicitly with --serial')
    return run([args.adb, '-s', args.serial, *words])


def extract(args):
    if not PACKAGE.fullmatch(args.package): raise ValueError('Invalid package')
    out = Path(args.out); out.mkdir(parents=True, exist_ok=False)
    target = adb(args, 'shell', 'cmd', 'package', 'resolve-activity', '--brief', '-a', 'android.intent.action.MAIN', '-c', 'android.intent.category.LAUNCHER', args.package)
    components = [line.strip() for line in target.splitlines() if re.fullmatch(r'[\w.$]+/[\w.$]+', line.strip())]
    if not components: raise ValueError('No launchable activity; do not guess a target')
    report = {'package': args.package, 'resolved_component': components[-1], 'raster_candidates': [],
              'foreground_candidates': [], 'xml_icons': [], 'apks': []}
    foreground_ids = set()
    paths = adb(args, 'shell', 'pm', 'path', args.package).splitlines()
    for i, line in enumerate(paths):
        if not line.startswith('package:'): continue
        apk = out/f'package-{i}.apk'; adb(args, 'pull', line[8:], str(apk))
        report['apks'].append({'file': apk.name, 'sha256': sha(apk.read_bytes())})
        badging = run([args.aapt2, 'dump', 'badging', apk]); (out/f'badging-{i}.txt').write_text(badging, encoding='utf-8')
        with zipfile.ZipFile(apk) as archive:
            found = set(re.findall(r"application-icon-(\d+):'([^']+)'", badging))
            for density, path in sorted(found):
                if path not in archive.namelist(): continue
                if Path(path).suffix.lower() in ('.png','.webp','.jpg','.jpeg'):
                    file = f'icon-{i}-{density}'+Path(path).suffix.lower()
                    (out/file).write_bytes(archive.read(path))
                    report['raster_candidates'].append({'file': file, 'density': int(density), 'apk': apk.name, 'resource': path})
                elif path.endswith('.xml'):
                    dump = run([args.aapt2, 'dump', 'xmltree', apk, '--file', path])
                    file = f'icon-{i}-{density}.xmltree.txt'; (out/file).write_text(dump, encoding='utf-8')
                    report['xml_icons'].append({'file': file, 'apk': apk.name, 'resource': path})
                    fg = re.search(r'E: foreground[^\n]*\n\s+A: [^\n]*drawable[^\n]*=@(0x[0-9a-fA-F]+)', dump)
                    if fg: foreground_ids.add(fg[1].lower())
    # Follow an adaptive icon's declared foreground resource, including a split
    # APK containing its density variant. Export that layer, never claim it is
    # a fully composed adaptive icon. Nested XML/vector rendering is a fallback.
    if foreground_ids:
        from PIL import Image
        for row in report['apks']:
            apk = out/row['file']
            resources = run([args.aapt2, 'dump', 'resources', apk])
            with zipfile.ZipFile(apk) as archive:
                for rid in foreground_ids:
                    match = re.search(r'(?m)^\s*resource '+re.escape(rid)+r' [^\n]+\n(?P<values>.*?)(?=^\s*resource |\Z)', resources, re.S | re.M)
                    if not match: continue
                    paths = re.findall(r'\(file\) (\S+) type=(?:PNG|WEBP|JPEG)', match['values'])
                    for resource in dict.fromkeys(paths):
                        if resource not in archive.namelist(): continue
                        data = archive.read(resource)
                        with Image.open(io.BytesIO(data)) as im: width, height = im.size
                        file = 'foreground-'+str(len(report['foreground_candidates']))+Path(resource).suffix.lower()
                        (out/file).write_bytes(data)
                        report['foreground_candidates'].append({'file': file, 'width': width, 'height': height,
                            'apk': apk.name, 'resource': resource, 'resource_id': rid, 'kind': 'adaptive_foreground_only'})
    if report['raster_candidates']:
        report['preferred_reference'] = max(report['raster_candidates'], key=lambda r:r['density'])['file']
        report['status'] = 'raster_extracted_review_before_redrawing'
    elif report['foreground_candidates']:
        report['preferred_reference'] = max(report['foreground_candidates'], key=lambda r:r['width']*r['height'])['file']
        report['status'] = 'adaptive_foreground_extracted_review_layer_not_full_icon'
    else:
        report['status'] = 'manual_reference_required_adaptive_xml_not_rasterized'
    write_json(out/'extraction.json', report); print(json.dumps(report, ensure_ascii=False, indent=2))


def install(args):
    apk = Path(args.apk).resolve(); meta = json.loads(apk.with_name('build.json').read_text())
    if not re.fullmatch(r'local\.monochrome\.entry\.[a-z][a-z0-9_]{1,39}', meta['entry_package']):
        raise ValueError('Only generated independent entry packages can be installed by this helper')
    if sha(apk.read_bytes()) != meta['sha256']: raise ValueError('APK changed after build')
    tc = tools(args)
    verification = run([tc['java'], '-jar', tc['apksigner'], 'verify', '--print-certs', apk])
    if meta['certificate_sha256'] not in verification: raise ValueError('Unexpected certificate')
    badging = run([tc['aapt2'], 'dump', 'badging', apk])
    if not re.search(r"^package: name='"+re.escape(meta['entry_package'])+"'", badging):
        raise ValueError('Manifest package does not match build metadata')
    if re.search(r'^uses-permission', badging, re.M): raise ValueError('Entry unexpectedly requests permissions')
    target = meta['target_package']+'/'+meta['target_activity']
    if not PACKAGE.fullmatch(meta['target_package']) or not ACTIVITY.fullmatch(meta['target_activity']): raise ValueError('Invalid target metadata')
    resolved = adb(args, 'shell', 'cmd', 'package', 'resolve-activity', '--brief', '-n', target)
    if meta['target_package']+'/' not in resolved: raise ValueError('Original app target is unavailable')
    result = adb(args, 'install', '-r', str(apk))
    if 'Success' not in result: raise ValueError(result)
    path = adb(args, 'shell', 'pm', 'path', meta['entry_package']).splitlines()[0].removeprefix('package:')
    remote_sha = adb(args, 'shell', 'sha256sum', shlex.quote(path)).split()[0]
    if remote_sha != meta['sha256']: raise ValueError('Installed APK hash differs')
    print('Installed and verified: '+meta['entry_package'])
    print('Select native Nothing themed icons, then test the entry and light/dark switching. No settings were changed.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    doctor = sub.add_parser('doctor'); doctor.add_argument('--adb', default='adb')
    ex = sub.add_parser('extract'); ex.add_argument('package'); ex.add_argument('--out', required=True)
    ex.add_argument('--aapt2', required=True); ex.add_argument('--adb', default='adb'); ex.add_argument('--serial', required=True)
    for name in ('init-key', 'build', 'install'):
        q = sub.add_parser(name)
        q.add_argument('--sdk', default=os.environ.get('ANDROID_HOME', ''))
        q.add_argument('--java-home', default=os.environ.get('JAVA_HOME', ''))
        q.add_argument('--api', type=int, default=36); q.add_argument('--build-tools', default='36.0.0')
        if name in ('init-key','build'): q.add_argument('--signing-dir', required=True)
        if name == 'build': q.add_argument('--config', required=True); q.add_argument('--out', required=True)
        if name == 'install':
            q.add_argument('--apk', required=True); q.add_argument('--adb', default='adb'); q.add_argument('--serial', required=True)
    args = p.parse_args()
    if args.command == 'doctor':
        print(run([args.adb, 'devices', '-l']))
        print('Expected: one authorized device. unauthorized → unlock and approve RSA; offline → reconnect. Multiple devices → select --serial.')
    elif args.command == 'extract': extract(args)
    elif args.command == 'init-key': identity(args, tools(args), create=True); print('Persistent local signing identity created. Back it up privately.')
    elif args.command == 'build': build_entry(args)
    elif args.command == 'install': install(args)


if __name__ == '__main__':
    try: main()
    except (ValueError, KeyError, OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print('Error: '+str(error), file=sys.stderr); sys.exit(1)
