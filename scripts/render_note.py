#!/usr/bin/env python3
"""Render evidence supplied in JSON to Markdown and optional Anki TSV."""
import argparse
from datetime import date
import difflib
import html
import json
from pathlib import Path
import re
import sys

MISSING = '未提供；不推断为已发生或已验证。'


def string(value, field, required=False):
    if value is None and not required:
        return None
    if not isinstance(value, str) or (required and not value.strip()):
        raise ValueError(f'{field} must be a non-empty string' if required else f'{field} must be a string or null')
    return value


def strings(value, field):
    if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
        raise ValueError(f'{field} must be an array of strings')
    return value


def validate(data):
    if not isinstance(data, dict):
        raise ValueError('input must be a JSON object')
    for key in ('title', 'date', 'topic'):
        string(data.get(key), key, True)
    if date.fromisoformat(data['date']).isoformat() != data['date']:
        raise ValueError('date must use YYYY-MM-DD')
    for key in ('context', 'error', 'before', 'after', 'cause', 'verification', 'language'):
        string(data.get(key), key)
    language = data.get('language') or 'python'
    if not re.fullmatch(r'[A-Za-z0-9_+-]+', language):
        raise ValueError('invalid code language')
    for key in ('sources', 'takeaways'):
        strings(data.get(key, []), key)
    cards = data.get('cards', [])
    if not isinstance(cards, list):
        raise ValueError('cards must be an array')
    for card in cards:
        if not isinstance(card, dict):
            raise ValueError('card must be an object')
        string(card.get('front'), 'card.front', True)
        string(card.get('back'), 'card.back', True)
        for tag in strings(card.get('tags', []), 'card.tags'):
            if not re.fullmatch(r'[\w-]+', tag):
                raise ValueError('card tags must be individual words')
    flow = data.get('flow')
    if flow is not None:
        if not isinstance(flow, dict) or not isinstance(flow.get('nodes'), list) or not isinstance(flow.get('edges'), list):
            raise ValueError('flow requires node and edge arrays')
        ids = set()
        for node in flow['nodes']:
            if not isinstance(node, dict):
                raise ValueError('flow node must be an object')
            node_id = string(node.get('id'), 'node.id', True)
            if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', node_id) or node_id in ids:
                raise ValueError('invalid or duplicate node id')
            ids.add(node_id)
            string(node.get('label'), 'node.label', True)
        for edge in flow['edges']:
            if not isinstance(edge, list) or len(edge) != 2 or any(not isinstance(x, str) or x not in ids for x in edge):
                raise ValueError('edge must reference two existing nodes')
    return data


def code_block(text, language=''):
    if text is None:
        return MISSING
    runs = [len(m.group()) for m in re.finditer(r'`+', text)]
    fence = '`' * max(3, max(runs, default=0) + 1)
    return f'{fence}{language}\n{text.rstrip()}\n{fence}'


def label(text):
    # Mermaid quoted labels accept numeric entities; never emit raw diagram syntax.
    return ''.join(f'#{ord(c)};' if c in '"<>&[]{}|`\\\r\n' else c for c in text)


def markdown(data):
    metadata = '\n'.join(f'{key}: {json.dumps(data[key], ensure_ascii=False)}' for key in ('title', 'date', 'topic'))
    parts = [f'---\n{metadata}\n---', f'# {data["title"].replace(chr(10), " ").replace(chr(13), " ")}',
             '## 来源与上下文', '\n'.join('- ' + s for s in data.get('sources', [])) or MISSING,
             data.get('context') or MISSING, '## 原始报错', code_block(data.get('error'), 'text'),
             '## 修改前代码', code_block(data.get('before'), data.get('language') or 'python'),
             '## 修改后或当前代码', code_block(data.get('after'), data.get('language') or 'python')]
    if data.get('before') is not None and data.get('after') is not None:
        difference = '\n'.join(difflib.unified_diff(data['before'].splitlines(), data['after'].splitlines(),
                                                  fromfile='before', tofile='after', lineterm=''))
        parts += ['## 代码差异', code_block(difference or '无文本差异', 'diff')]
    parts += ['## 原因与不确定项', data.get('cause') or MISSING,
              '## 验证记录', data.get('verification') or MISSING,
              '## 流程图']
    flow = data.get('flow')
    if flow and flow['nodes']:
        lines = ['flowchart TD']
        lines += [f'    {node["id"]}["{label(node["label"])}"]' for node in flow['nodes']]
        lines += [f'    {a} --> {b}' for a, b in flow['edges']]
        parts.append(code_block('\n'.join(lines), 'mermaid'))
    else:
        parts.append('未提供已核实的流程结构。')
    parts += ['## 关键知识', '\n'.join('- ' + s for s in data.get('takeaways', [])) or MISSING,
              '## 复习问答']
    for i, card in enumerate(data.get('cards', []), 1):
        parts += [f'### {i}. {card["front"]}', card['back']]
    if not data.get('cards'):
        parts.append('尚无可核实的复习卡片。')
    return '\n\n'.join(parts) + '\n'


def anki(data):
    def field(text):
        return html.escape(text).replace('\r\n', '\n').replace('\r', '\n').replace('\n', '<br>').replace('\t', '&#9;')
    lines = ['#separator:tab', '#html:true', '#columns:Front\tBack\tTags', '#tags column:3']
    for card in data.get('cards', []):
        lines.append('\t'.join([field(card['front']), field(card['back']), ' '.join(card.get('tags', []))]))
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--name', required=True, help='ASCII slug; no paths')
    parser.add_argument('--anki', action='store_true')
    args = parser.parse_args()
    try:
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', args.name):
            raise ValueError('name must be an ASCII slug with no path separators')
        data = validate(json.loads(args.input.read_text(encoding='utf-8-sig')))
        stem = data['date'] + '-' + args.name
        output = args.output_dir.resolve()
        targets = {output / (stem + '.md'): markdown(data)}
        if args.anki:
            targets[output / (stem + '.anki.tsv')] = anki(data)
        if any(path.exists() for path in targets):
            raise ValueError('output already exists; choose a new name')
        output.mkdir(parents=True, exist_ok=True)
        created = []
        try:
            for path, content in targets.items():
                with path.open('x', encoding='utf-8', newline='\n') as handle:
                    created.append(path)
                    handle.write(content)
        except OSError:
            for path in created:
                path.unlink(missing_ok=True)
            raise
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        print(json.dumps({'files': [str(p) for p in targets], 'archive_connected': False,
                          'anki_imported': False}, ensure_ascii=False))
    except (ValueError, OSError, TypeError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
