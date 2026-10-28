"""Refresh public repository activity. Never reads private repos or commit content."""
import datetime as dt
import html
import json
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
START, END = '<!-- PUBLIC_ACTIVITY:START -->', '<!-- PUBLIC_ACTIVITY:END -->'
OWNER = 'ahansardar'


def public_json(path):
    # Deliberately unauthenticated: private repository data is inaccessible.
    req = urllib.request.Request('https://api.github.com' + path, headers={
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'ahansardar-profile-public-activity',
        'X-GitHub-Api-Version': '2022-11-28',
    })
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)


def safe_words(value):
    return html.escape(str(value), quote=True).replace('\n', ' ').replace('\r', ' ')


def public_repositories(fetch=public_json):
    repos = []
    for page in range(1, 21):
        batch = fetch(f'/users/{OWNER}/repos?type=owner&sort=pushed&direction=desc&per_page=100&page={page}')
        if not isinstance(batch, list):
            raise ValueError('Expected a repository list.')
        for r in batch:
            # Defense in depth, even though the anonymous endpoint is public-only.
            if r.get('private') is not False or r.get('visibility', 'public') != 'public':
                raise ValueError('Unexpected private repository data.')
            if r.get('owner', {}).get('login', '').lower() != OWNER:
                raise ValueError('Unexpected repository owner.')
            if not re.fullmatch(r'[A-Za-z0-9_.-]+', r.get('name', '')):
                raise ValueError('Unexpected repository name.')
            if r.get('html_url') != f'https://github.com/{OWNER}/{r["name"]}':
                raise ValueError('Unexpected repository URL.')
            repos.append(r)
        if len(batch) < 100:
            return repos
    raise ValueError('Pagination limit reached. Do not publish a partial directory.')


def repo_link(r):
    labels = []
    if r.get('fork'):
        labels.append('fork')
    if r.get('archived'):
        labels.append('archived')
    suffix = ' (' + ', '.join(labels) + ')' if labels else ''
    return f'<a href="{html.escape(r["html_url"], quote=True)}">{safe_words(r["name"])}</a>{suffix}'


def build_section(repos, today=None):
    checked = today or dt.datetime.now(dt.timezone.utc).date().isoformat()
    recent = sorted((r for r in repos if r['name'].lower() != OWNER and r.get('pushed_at')),
                    key=lambda r:r['pushed_at'], reverse=True)[:6]
    lines = ['<p>Recent pushes across my public repositories. This is activity, not a claim that every project is my current focus.</p>', '<ul>']
    for r in recent:
        when = dt.datetime.fromisoformat(r['pushed_at'].replace('Z', '+00:00'))
        lines.append(f'<li>{repo_link(r)} - last push {when:%d %b %Y, %H:%M} UTC</li>')
    lines += ['</ul>', f'<p>Public repository data last checked: {checked} (UTC). Refreshes about hourly; GitHub can delay scheduled runs.</p>',
              '<details>', f'<summary>All public repositories ({len(repos)})</summary>', '<ul>']
    for r in sorted(repos,key=lambda r:r['name'].lower()):
        lines.append('<li>' + repo_link(r) + '</li>')
    lines += ['</ul>', '</details>', '<sub>Private repositories are excluded. Forks and archived repositories are labelled. The profile repository appears in the directory but not in recent pushes, so its automatic updates do not drown out project activity.</sub>']
    return '\n'.join(lines)


def update_readme(text, section):
    if text.count(START) != 1 or text.count(END) != 1 or text.index(START) >= text.index(END):
        raise ValueError('Expected exactly one ordered marker pair.')
    before, rest = text.split(START)
    _, after = rest.split(END)
    return before + START + '\n' + section + '\n' + END + after




def activity_svg(repos, today=None):
    """Self-contained graphic using only public names and pushed-at times."""
    import textwrap
    checked = today or dt.datetime.now(dt.timezone.utc).date().isoformat()
    recent = sorted((r for r in repos if r['name'].lower() != OWNER and r.get('pushed_at')),
                    key=lambda r:r['pushed_at'], reverse=True)[:6]
    height = 220 + len(recent) * 106
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="{height}" viewBox="0 0 800 {height}">',
           f'<rect width="800" height="{height}" fill="#f5f2e9"/>',
           '<text x="36" y="43" font-family="monospace" font-size="20" fill="#595b52">01 / PUBLIC REPOSITORY ACTIVITY</text>',
           '<text x="34" y="110" font-family="Arial,sans-serif" font-size="56" font-weight="700" letter-spacing="-2" fill="#25251f">On my workbench, lately.</text>']
    for i,r in enumerate(recent):
        y=147+i*106
        bg=['#f4e5ae','#d8e1c9','#ecd7be'][i%3]
        out.append(f'<rect x="24" y="{y}" width="752" height="94" fill="{bg}"/>')
        name=r['name']
        # Bound rendered text while the full name/link remains in accessible details.
        name = name if len(name)<=43 else name[:40]+'...'
        out.append(f'<text x="43" y="{y+37}" font-family="Arial,sans-serif" font-size="29" font-weight="700" fill="#25251f">{safe_words(name)}</text>')
        when=dt.datetime.fromisoformat(r['pushed_at'].replace('Z','+00:00'))
        suffix=' / fork' if r.get('fork') else ''
        suffix+=' / archived' if r.get('archived') else ''
        out.append(f'<text x="43" y="{y+72}" font-family="monospace" font-size="22" fill="#595b52">Last push {when:%d %b %Y, %H:%M} UTC{suffix}</text>')
    y=height-45
    out += [f'<text x="36" y="{y}" font-family="monospace" font-size="20" fill="#595b52">{len(repos)} public repos / checked {checked} UTC</text>',
            '<text x="36" y="'+str(y+29)+'" font-family="Arial,sans-serif" font-size="21" fill="#595b52">Hourly refresh. Activity is not current focus.</text>', '</svg>']
    return '\n'.join(out)



DARK_PALETTE = {'#f5f2e9': '#181c20', '#25251f': '#eee9de', '#595b52': '#b4b7ad', '#ba4529': '#e39173', '#f4e5ae': '#393526', '#d8e1c9': '#29372e', '#ecd7be': '#3b302c', '#62604d': '#b7b29c', '#e5e1d9': '#343a3e', '#fff5df': '#f2d9c4'}


def dark_svg(svg):
    return re.sub(r'#[0-9a-fA-F]{6}', lambda match: DARK_PALETTE.get(match[0], match[0]), svg)


if __name__ == '__main__':
    repos = public_repositories()
    section = '<picture><source media="(prefers-color-scheme: dark)" srcset="./assets/public-activity-mobile-dark.svg" /><source media="(max-width: 600px)" srcset="./assets/public-activity-mobile.svg" /><img width="100%" src="./assets/public-activity.svg" alt="Recent public repository pushes, with dates. Expand the text version below for accessible links." /></picture>\n\n<details>\n<summary><b>Activity links, dates and all public repositories</b></summary>\n\n' + build_section(repos) + '\n</details>'
    readme = ROOT / 'README.md'
    updated = update_readme(readme.read_text(), section)
    graphic = activity_svg(repos)
    mobile_graphic = graphic.replace('width="800"', 'width="600"').replace('viewBox="0 0 800', 'viewBox="0 0 600').replace('width="752"', 'width="552"').replace('font-size="56"', 'font-size="40"').replace('font-size="29"', 'font-size="25"').replace('font-size="22"', 'font-size="19"')
    import xml.etree.ElementTree as ET
    tree = ET.fromstring(mobile_graphic)
    for element in tree.iter('{http://www.w3.org/2000/svg}text'):
        text = element.text or ''
        if element.get('font-weight') == '700' and element.get('font-size') == '25' and len(text) > 34:
            element.text = text[:31] + '...'
        if text.startswith('Last push '):
            element.text = text.split(' / ')[0]
    mobile_graphic = ET.tostring(tree, encoding='unicode')
    (ROOT / 'assets/public-activity.svg').write_text(graphic)
    (ROOT / 'assets/public-activity-mobile.svg').write_text(mobile_graphic)
    (ROOT / 'assets/public-activity-dark.svg').write_text(dark_svg(graphic))
    (ROOT / 'assets/public-activity-mobile-dark.svg').write_text(dark_svg(mobile_graphic))
    readme.write_text(updated)
