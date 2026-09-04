import json
import os
import shutil
import subprocess
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "_work")
RAW = os.path.join(WORK, "raw")
OUT = os.path.join(ROOT, "media")
ARCHIVES = [os.path.join(WORK, "cz1.zip"), os.path.join(WORK, "cz2.zip")]

VIDEO_SCALE = "'min(1024,iw)':-2"
VIDEO_CRF = "30"
IMAGE_MAX = 1280
IMAGE_Q = "4"
JOBS = max(2, (os.cpu_count() or 4))


def ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    base = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Packages")
    for dirpath, _dirnames, filenames in os.walk(base):
        if "ffmpeg.exe" in filenames:
            return os.path.join(dirpath, "ffmpeg.exe")
    raise SystemExit("ffmpeg not found")


FFMPEG = ffmpeg()


def wanted():
    with open(os.path.join(ROOT, "data", "questions.json"), encoding="utf-8") as f:
        data = json.load(f)
    names = {}
    for q in data["questions"]:
        m = q.get("media")
        if m:
            names[m["orig"]] = m["src"]
    return names


def extract(names):
    os.makedirs(RAW, exist_ok=True)
    found = {}
    for path in ARCHIVES:
        if not os.path.exists(path):
            print("missing archive:", path)
            continue
        with zipfile.ZipFile(path) as z:
            for info in z.infolist():
                if info.is_dir():
                    continue
                base = os.path.basename(info.filename)
                if base in names and base not in found:
                    target = os.path.join(RAW, base)
                    if not os.path.exists(target):
                        with z.open(info) as src, open(target, "wb") as dst:
                            shutil.copyfileobj(src, dst)
                    found[base] = target
        print(os.path.basename(path), "->", len(found), "files so far")
    return found


def convert_video(src, dst):
    cmd = [
        FFMPEG, "-y", "-v", "error", "-i", src,
        "-vf", "scale=" + VIDEO_SCALE + ":flags=bicubic",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", VIDEO_CRF,
        "-profile:v", "main", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", "-an", dst
    ]
    return subprocess.run(cmd, capture_output=True).returncode


def convert_image(src, dst):
    cmd = [
        FFMPEG, "-y", "-v", "error", "-i", src,
        "-vf", "scale='min(%d,iw)':-2:flags=bicubic" % IMAGE_MAX,
        "-q:v", IMAGE_Q, dst
    ]
    return subprocess.run(cmd, capture_output=True).returncode


def main():
    names = wanted()
    print("media referenced by kat. B questions:", len(names))

    found = extract(names)
    missing = [n for n in names if n not in found]
    print("extracted:", len(found), "| not in archives:", len(missing))
    if missing:
        with open(os.path.join(WORK, "missing_media.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(missing)))

    os.makedirs(OUT, exist_ok=True)
    jobs = []
    for orig, src in found.items():
        dst = os.path.join(OUT, names[orig])
        if os.path.exists(dst) and os.path.getsize(dst) > 0:
            continue
        jobs.append((orig, src, dst))

    print("to convert:", len(jobs), "with", JOBS, "workers")
    done = [0]

    def run(job):
        orig, src, dst = job
        if orig.lower().endswith(".wmv"):
            rc = convert_video(src, dst)
        else:
            rc = convert_image(src, dst)
        done[0] += 1
        if done[0] % 50 == 0:
            print(done[0], "/", len(jobs), flush=True)
        return (orig, rc)

    failed = []
    with ThreadPoolExecutor(max_workers=JOBS) as pool:
        for orig, rc in pool.map(run, jobs):
            if rc != 0:
                failed.append(orig)

    total = 0
    for name in os.listdir(OUT):
        total += os.path.getsize(os.path.join(OUT, name))
    print("failed:", len(failed))
    if failed:
        print("  ", failed[:10])
    print("files in media/:", len(os.listdir(OUT)))
    print("total size: %.1f MB" % (total / 1048576.0))


if __name__ == "__main__":
    main()
