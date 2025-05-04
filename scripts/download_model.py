import requests, sys, pathlib, hashlib

URL = "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth"
TARGET = pathlib.Path(sys.argv[1]).expanduser()

TARGET.parent.mkdir(parents=True, exist_ok=True)
if TARGET.exists(): sys.exit(0)          # already downloaded

print("Downloading SAM checkpoint …")
data = requests.get(URL, stream=True, timeout=60)
data.raise_for_status()
with open(TARGET, "wb") as f:
    for chunk in data.iter_content(1 << 20):
        f.write(chunk)

print("Finished:", TARGET, "SHA256:", hashlib.sha256(TARGET.read_bytes()).hexdigest()[:12])