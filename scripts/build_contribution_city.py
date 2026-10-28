import re,pathlib,html,json,datetime,collections
import urllib.request
ROOT = pathlib.Path(__file__).resolve().parents[1]
p = ROOT / 'profile-city'
p.mkdir(exist_ok=True)
request = urllib.request.Request('https://github.com/users/ahansardar/contributions', headers={'User-Agent': 'ahansardar-contribution-city'})
with urllib.request.urlopen(request, timeout=30) as response:
    s = response.read().decode('utf-8')
rows=[]
for m in re.finditer(r'<td\b[^>]*data-date="([^"]+)"[^>]*id="([^"]+)"[^>]*data-level="([^"]+)"[^>]*>',s):
 date,id,level=m.groups();t=re.search(r'<tool-tip\b[^>]*for="'+id+r'"[^>]*>(.*?)</tool-tip>',s,re.S)
 if not t:raise ValueError('Missing count')
 label=html.unescape(re.sub('<[^>]+>','',t[1])).strip();count=0 if label.startswith('No ') else int(re.match(r'([\d,]+)',label)[1].replace(',',''))
 rows.append({'date':date,'count':count,'level':int(level)})
rows.sort(key=lambda r:r['date'])
# Fail closed rather than replacing a good city with a partial/changed page.
if not 350 <= len(rows) <= 380 or len({d['date'] for d in rows}) != len(rows):
    raise ValueError('Unexpected contribution calendar size or duplicate dates')
for i, day in enumerate(rows):
    date = datetime.date.fromisoformat(day['date'])
    if day['count'] < 0 or day['level'] not in range(5):
        raise ValueError('Unexpected contribution count or level')
    if i and (date-datetime.date.fromisoformat(rows[i-1]['date'])).days != 1:
        raise ValueError('Contribution dates are not contiguous')
(p/'contribution-days.json').write_text(json.dumps(rows,indent=2))
import math
N=28; H=math.ceil(len(rows)/N)
for dark in [True,False]:
 bg='#181c20' if dark else '#f5f2e9';ink='#eee9de' if dark else '#25251f';muted='#b4b7ad' if dark else '#595b52';ground='#242c2d' if dark else '#d9dfd0';road='#141a1d' if dark else '#bbbdb5';park='#314b3d' if dark else '#a7be99'
 out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="940" viewBox="0 0 1200 940"><rect width="1200" height="940" fill="{bg}"/>',f'<text x="44" y="46" font-family="monospace" font-size="16" fill="{muted}">AHAN / A YEAR, BUILT DAY BY DAY</text>',f'<text x="42" y="100" font-family="Arial" font-weight="700" font-size="44" fill="{ink}">Contribution city.</text>',f'<text x="44" y="137" font-family="Arial" font-size="18" fill="{muted}">An illustrated city built from the public contribution calendar.</text>']
 out.append('<defs><path id="window" d="M0,0l3,1.5v3l-3,-1.5z" fill="'+('#efd7a0' if dark else '#555e5b')+'"/></defs>')
 def xy(x,y,z=0):return (390+x*18-y*18,240+x*9+y*9-z)
 def poly(points,color,stroke=None):
  coords=' '.join(f'{a:.1f},{b:.1f}' for a,b in points);out.append(f'<polygon points="{coords}" fill="{color}"'+(f' stroke="{stroke}" stroke-width=".7"' if stroke else '')+'/>')
 def tile(x,y,w,h,col,z=0):poly([xy(x,y,z),xy(x+w,y,z),xy(x+w,y+h,z),xy(x,y+h,z)],col)
 # Broad city slab, street grid, lane markers and landscaped empty lots.
 W=N+N//4*.65;D=H+H//3*.65
 tile(-1,-1,W+2,D+2,ground)
 for c in range(4,N,4):
  x=c+(c//4-1)*.65;tile(x,0,.65,D,road)
  for y in range(int(D)):tile(x+.3,y+.22,.05,.38,muted)
 for r in range(3,H,3):
  y=r+(r//3-1)*.65;tile(0,y,W,.65,road)
  for x in range(int(W)):tile(x+.2,y+.3,.38,.05,muted)
 # Draw back to front for correct occlusion.
 lots=[]
 for i,day in enumerate(rows):
  c=i%N;r=i//N;x=c+(c//4)*.65;y=r+(r//3)*.65;lots.append((x+y,x,y,day))
 for _,x,y,day in sorted(lots):
  count=day['count'];out.append(f'<g><title>{day["date"]}: {count} contributions</title>')
  if not count:
   tile(x+.1,y+.1,.8,.8,park)
   # zero-activity days are small planted squares, not fabricated buildings.
   if int(day['date'][-2:])%3==0:
    a,b=xy(x+.5,y+.5);out.append(f'<path d="M{a},{b}v-8" stroke="{muted}"/><circle cx="{a}" cy="{b-10}" r="3" fill="{park}" stroke="{muted}" stroke-width=".5"/>')
  else:
   z=8+math.log2(count+1)*9
   top=['#bfa574','#cfaa7b','#cc8e71','#d8b096'][day['level']-1] if dark else ['#d9be87','#c7a580','#b7866d','#e0bb8e'][day['level']-1]
   left='#78624e' if dark else '#a48569';right='#574c42' if dark else '#8b735e';a=x+.12;b=y+.12;w=.76;d=.76
   poly([xy(a,b+d),xy(a+w,b+d),xy(a+w,b+d,z),xy(a,b+d,z)],left)
   poly([xy(a+w,b),xy(a+w,b+d),xy(a+w,b+d,z),xy(a+w,b,z)],right)
   tile(a,b,w,d,top,z)
   # Windows, roof equipment and alternating storefront awnings.
   for h in range(5,int(z)-3,7):
    for step in [.23,.52]:
     xx,yy=xy(a+step,b+d,h);out.append(f'<use href="#window" x="{xx:.1f}" y="{yy:.1f}"/>')
   if count>12:tile(a+.25,b+.22,.22,.26,muted,z+3)
  out.append('</g>')
 total=sum(r['count'] for r in rows);active=sum(r['count']>0 for r in rows)
 out += [f'<text x="44" y="830" font-family="Arial" font-size="20" fill="{ink}">{total:,} contributions · {active} active days · {rows[0]["date"]} to {rows[-1]["date"]}</text>',f'<text x="44" y="864" font-family="Arial" font-size="17" fill="{muted}">One lot = one date, oldest to newest, row by row. Taller building = more contributions.</text>',f'<text x="44" y="891" font-family="Arial" font-size="17" fill="{muted}">Green lots = zero days. Roads, trees and windows are decorative. Height uses a log scale.</text>',f'<text x="44" y="921" font-family="monospace" font-size="14" fill="{muted}">PUBLIC CALENDAR / NOT A REAL-WORLD MAP</text>','</svg>']
 (p/('city-dark.svg' if dark else 'city-light.svg')).write_text(''.join(out))
readme = ROOT / 'README.md'
text = readme.read_text()
start, end = '<!-- CONTRIBUTION_CITY:START -->', '<!-- CONTRIBUTION_CITY:END -->'
if text.count(start) != 1 or text.count(end) != 1:
    raise ValueError('Missing city marker pair')
section = f'''<picture><source media="(prefers-color-scheme: dark)" srcset="./profile-city/city-dark.svg" /><img width="100%" src="./profile-city/city-light.svg" alt="Illustrated contribution city: buildings represent active dates, green lots represent zero days, and building height increases with contributions." /></picture>

**{total:,} contributions across {active} active dates** · {rows[0]['date']} to {rows[-1]['date']}.

Each plot is one date, oldest to newest, row by row. Taller buildings mean more contributions, using a logarithmic scale. Green plots are zero days. Roads, trees, windows and roof details are decoration, not extra activity.

[Open dark city full-size](./profile-city/city-dark.svg) · [Open light city full-size](./profile-city/city-light.svg) · [Daily contribution data](./profile-city/contribution-days.json)

Built daily from the publicly visible GitHub contribution calendar. This can include anonymous private-contribution counts if enabled on my profile. No private repository details are read. GitHub activity is not a measure of skill.

[Original contribution city](./profile-3d-contrib/profile-season-animate.svg) · [Achievements tracker](./ACHIEVEMENTS_TRACKER.md)'''
before, rest = text.split(start)
_, after = rest.split(end)
readme.write_text(before + start + '\n' + section + '\n' + end + after)
print(f'Built city from {len(rows)} dates, {total} contributions')
