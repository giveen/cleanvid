# 🚀 run_cleanvid.sh

This script provides an interactive way to run `cleanvid` inside a GPU-accelerated Docker container. It supports:

- ✅ Tab-completion for video files
- ✅ Automatic detection of matching `.srt` subtitle files
- ✅ Fallback to subtitle download via `subliminal` if no `.srt` is found
- ✅ Full NVIDIA NVENC support via mounted runtime libraries

---

## 📦 Prerequisites

- Docker installed
- NVIDIA GPU with driver version ≥ 570.0
- NVIDIA Container Toolkit installed
- Required runtime libraries available on host:
  - `/usr/lib/x86_64-linux-gnu/libnvidia-encode.so.1`
  - `/usr/lib/x86_64-linux-gnu/libnvcuvid.so.1`

---

## 🛠️ Setup

Place this script in the `docker/` folder of your cleanvid repo:

```bash
chmod +x run_cleanvid.sh
```

---

## 🎬 Usage

From the `docker/` folder:

```bash
./run_cleanvid.sh
```

You’ll be prompted to select a video file. The script will:

1. Look for a matching `.srt` file
2. If not found, attempt to download subtitles using `subliminal`
3. Run `cleanvid` inside the container with GPU acceleration
4. Output a cleaned video file named `EXAMPLE.clean.mp4`

---

## 🧪 Example Output

```bash
🎬 Available video files:
1) EXAMPLE.mp4
# Select file by number

📝 Found matching subtitle file: EXAMPLE.srt
🚀 Running cleanvid with GPU acceleration...
✅ Output created: EXAMPLE.clean.mp4
```

---

## 🛠️ Debugging

If subtitle download fails, make sure the video filename is well-formed and your internet connection is active. You can also run the container manually:

```bash
sudo docker run --rm --gpus all \
  -v "$PWD:/videos" \
  -v /usr/lib/x86_64-linux-gnu/libnvidia-encode.so.1:/usr/lib/x86_64-linux-gnu/libnvidia-encode.so.1:ro \
  -v /usr/lib/x86_64-linux-gnu/libnvcuvid.so.1:/usr/lib/x86_64-linux-gnu/libnvcuvid.so.1:ro \
  --entrypoint ffmpeg \
  oci.guero.org/cleanvid:gpu -encoders | grep nvenc
```

---

## 📄 License

This script is part of the [cleanvid](https://github.com/mmguero/cleanvid) project and follows the BSD 3-Clause License.

---
