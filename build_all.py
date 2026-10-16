# 두 페이지를 한 번에 다시 만든다. 사용: python3 build_all.py
# 스포2 일정 원본: shared/sf2_schedule.py / 스포2 본문: sf2/sf2-web-guide.html / 서비스개발실 데이터: svcdev/data.py
import subprocess, sys, os
R = os.path.dirname(os.path.abspath(__file__))
for cmd, cwd in ((['python3', 'gantt2.py'], 'sf2'), (['python3', 'msfix.py'], 'sf2'), (['python3', 'build.py'], 'svcdev')):
    r = subprocess.run(cmd, cwd=os.path.join(R, cwd))
    if r.returncode: sys.exit(r.returncode)
print('built: sf2/sf2-web-guide.html, svcdev/web-ops.html')
