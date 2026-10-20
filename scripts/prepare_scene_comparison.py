"""CI-only baseline/current builds sharing one public offer snapshot; no API secrets."""
import io
import os
import re
import subprocess
import tarfile
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parents[1]
base_sha = os.environ['SCENE_BASE_SHA']
if not re.fullmatch(r'[0-9a-f]{40}',base_sha):
    raise ValueError('Expected a complete base commit SHA')
baseline = root/'audit-results'/'baseline'
baseline.mkdir(parents=True,exist_ok=True)
archive = subprocess.check_output(['git','archive',base_sha],cwd=root)
with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
    tar.extractall(baseline,filter='data')
with urllib.request.urlopen('https://stusaurus.github.io/kyo-bodo-jp/data/rakuten.json',timeout=30) as response:
    offers = response.read()
for directory in (baseline,root):
    (directory/'data'/'rakuten_cache.json').write_bytes(offers)
    subprocess.run(['python',str(directory/'scripts'/'build_site.py')],cwd=directory,check=True)
