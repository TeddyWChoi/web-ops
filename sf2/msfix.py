import re, os, sys
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'shared'))
from sf2_schedule import SF2_MS_LABELS
p=os.path.join(HERE,'sf2-web-guide.html')
s=open(p,encoding='utf-8').read()
m=re.search(r'<tr class="g-group"><td class="g-name" colspan="2"><b>마일스톤</b></td><td class="g-track"><div class="g-lane" style="width:(\d+)px">(.*?)<span class="g-today"',s,flags=re.S)
inner=m.group(2)
dias=re.findall(r'<span class="g-ms" style="left:(\d+)px" title="([^"]+)"></span>',inner)
labels=SF2_MS_LABELS
new=''
for left,title in dias:
    key=title.split()[0]
    txt,al,top=labels[key]
    L=int(left)
    new+=f'<span class="g-ms" style="left:{L}px;top:{top+2}px" title="{title}"></span>'
    if al=='l': new+=f'<span class="g-mslabel" style="left:{L+10}px;top:{top}px">{txt}</span>'
    else: new+=f'<span class="g-mslabel" style="left:{L-10}px;top:{top}px;transform:translateX(-100%)">{txt}</span>'
s=s[:m.start(2)]+new+s[m.end(2):]
s=s.replace('<tr class="g-group"><td class="g-name" colspan="2"><b>마일스톤</b></td><td class="g-track"><div class="g-lane"','<tr class="g-group g-msrow"><td class="g-name" colspan="2"><b>마일스톤</b></td><td class="g-track"><div class="g-lane"')
if 'tr.g-msrow .g-lane' not in s:
    s=s.replace('.g-ms {','tr.g-msrow .g-lane { height: 46px; }\n.g-ms {',1)
open(p,'w',encoding='utf-8').write(s)
print(len(dias))
