import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('icons', ROOT/'skills/nothing-monochrome-entries/scripts/icons.py')
icons = importlib.util.module_from_spec(spec); spec.loader.exec_module(icons)


class EntryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        im = Image.new('RGB', (200, 200), 'black')
        ImageDraw.Draw(im).ellipse((50, 50, 150, 150), fill='white')
        im.save(self.root/'source.png')
        self.value = {'slug':'demo', 'label':'Demo " & 测试', 'target_package':'com.example.app',
                      'target_activity':'.LauncherAlias', 'version_code':1, 'artwork':'source.png'}

    def load(self):
        p = self.root/'config.json'; p.write_text(json.dumps(self.value))
        return icons.config(p)

    def test_explicit_target_alias_and_separate_identity(self):
        c = self.load()
        self.assertEqual(c['target_activity'], 'com.example.app.LauncherAlias')
        self.assertNotEqual(c['entry_package'], c['target_package'])
        self.assertEqual(c['artwork'], str((self.root/'source.png').resolve()))

    def test_shell_metacharacters_cannot_enter_components(self):
        for name in ['slug','target_package','target_activity']:
            with self.subTest(field=name):
                old = self.value[name]; self.value[name] = 'com.example;echo bad'
                with self.assertRaises(ValueError): self.load()
                self.value[name] = old

    def test_self_target_and_invalid_version_rejected(self):
        self.value['target_package'] = 'local.monochrome.entry.demo'
        with self.assertRaises(ValueError): self.load()
        self.value['target_package'] = 'com.example.app'; self.value['version_code'] = 0
        with self.assertRaises(ValueError): self.load()

    def test_mask_has_transparent_corners_and_unchanged_source(self):
        before = (self.root/'source.png').read_bytes()
        data, meta = icons.render(self.load())
        im = Image.open(io.BytesIO(data))
        self.assertEqual(im.mode, 'RGBA'); self.assertEqual(im.size, (432,432))
        self.assertEqual(im.getpixel((0,0))[3], 0)
        self.assertGreater(im.getpixel((216,216))[3], 250)
        self.assertLess(meta['max_radius_px'], 144)
        self.assertEqual(before, (self.root/'source.png').read_bytes())

    def test_opaque_input_cannot_silently_become_alpha_square(self):
        self.value['input_mode'] = 'alpha'
        with self.assertRaisesRegex(ValueError, 'actual transparency'): icons.render(self.load())

    def test_oversize_and_empty_masks_rejected(self):
        self.value['scale_percent'] = 150
        with self.assertRaisesRegex(ValueError, 'circular mask'): icons.render(self.load())
        Image.new('RGB', (20,20), 'black').save(self.root/'source.png')
        with self.assertRaisesRegex(ValueError, 'No visible'): icons.render(self.load())


if __name__ == '__main__': unittest.main()
