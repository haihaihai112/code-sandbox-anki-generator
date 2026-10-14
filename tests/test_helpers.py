import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
XRAY = ROOT / 'scripts' / 'repo_xray.py'
NOTE = ROOT / 'scripts' / 'render_note.py'
DOCTOR = ROOT / 'scripts' / 'env_doctor.ps1'

class HelperTests(unittest.TestCase):
    def run_python(self, script, *args):
        return subprocess.run([sys.executable, '-I', str(script), *map(str, args)],
                              text=True, encoding='utf-8', capture_output=True, timeout=30)

    def test_note_export_preserves_uncertainty_and_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            data = {'title': 'Tensor reshape', 'date': '2026-10-14', 'topic': 'pytorch',
                    'sources': ['user supplied corrected snippet'], 'error': None,
                    'before': None, 'after': 'x.reshape(2, 3)', 'cause': None,
                    'verification': None, 'takeaways': ['reshape must preserve element count'],
                    'flow': {'nodes': [{'id': 'A', 'label': 'Count elements'},
                                       {'id': 'B', 'label': 'Reshape'}],
                             'edges': [['A', 'B']]},
                    'cards': [{'front': 'What does <reshape> preserve?\nExplain.',
                               'back': 'The number of elements.\tNo copy guarantee.',
                               'tags': ['pytorch', 'shape']} ]}
            source = base / 'input.json'
            source.write_text(json.dumps(data), encoding='utf-8')
            result = self.run_python(NOTE, source, '--output-dir', base / 'notes', '--name', 'shape', '--anki')
            self.assertEqual(result.returncode, 0, result.stderr)
            md = (base / 'notes' / '2026-10-14-shape.md').read_text(encoding='utf-8')
            self.assertIn('未提供', md)
            self.assertIn('```mermaid', md)
            tsv = (base / 'notes' / '2026-10-14-shape.anki.tsv').read_text(encoding='utf-8')
            line = next(line for line in tsv.splitlines() if not line.startswith('#'))
            self.assertEqual(len(line.split('\t')), 3)
            self.assertIn('&lt;reshape&gt;', line)
            again = self.run_python(NOTE, source, '--output-dir', base / 'notes', '--name', 'shape', '--anki')
            self.assertNotEqual(again.returncode, 0)
            self.assertEqual(md, (base / 'notes' / '2026-10-14-shape.md').read_text(encoding='utf-8'))

    def test_note_rejects_path_escape_and_unknown_mermaid_node(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'input.json'
            source.write_text(json.dumps({'title': 'Test', 'date': '2026-10-14', 'topic': 'sql',
                                         'cards': [], 'flow': {'nodes': [{'id': 'A', 'label': 'a'}],
                                                               'edges': [['A', 'MISSING']]}}), encoding='utf-8')
            result = self.run_python(NOTE, source, '--output-dir', Path(tmp) / 'notes', '--name', '../escape')
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((Path(tmp) / 'escape.md').exists())
            result = self.run_python(NOTE, source, '--output-dir', Path(tmp) / 'notes', '--name', 'safe')
            self.assertNotEqual(result.returncode, 0)

if __name__ == '__main__':
    unittest.main(verbosity=2)
