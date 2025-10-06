# 🧼 cleanvid

[![Latest Version](https://img.shields.io/pypi/v/cleanvid)](https://pypi.python.org/pypi/cleanvid/) [![Docker Image](https://github.com/mmguero/cleanvid/workflows/cleanvid-build-push-ghcr/badge.svg)](https://github.com/mmguero/cleanvid/pkgs/container/cleanvid)

**cleanvid** is a script to mute profanity in video files using subtitle-based detection and audio stream editing. It works in four steps:

1. You provide a video file and matching `.srt` subtitle file. If subtitles aren’t provided, cleanvid will extract them or use [`subliminal`](https://github.com/Diaoul/subliminal) to download the best match.
2. [`pysrt`](https://github.com/byroot/pysrt) parses the `.srt` file and checks each entry against a [list](./src/cleanvid/swears.txt) of objectionable words. You can provide mappings (e.g., "sh*t" → "poop") or let cleanvid replace them with `*****`.
3. A new "clean" `.srt` file is created with only the censored phrases.
4. [`ffmpeg`](https://www.ffmpeg.org/) is used to mute the audio stream during those segments. The cleaned audio is re-encoded and remuxed with the original video. Optionally, the clean `.srt` file can be embedded as a subtitle track.

You can then play the cleaned video with your favorite media player.

As an alternative to creating a new video file, cleanvid can generate:
- An [EDL file](http://www.mplayerhq.hu/DOCS/HTML/en/edl.html) for MPlayer or Kodi
- A JSON definition file for [PlexAutoSkip](https://github.com/mdhiggins/PlexAutoSkip)

**cleanvid** is part of a family of censorship tools:

* 📼 [cleanvid](https://github.com/mmguero/cleanvid) for video files
* 🎤 [monkeyplug](https://github.com/mmguero/monkeyplug) for audio/video using Whisper or Vosk
* 📕 [montag](https://github.com/mmguero/montag) for ebooks

---

## 📦 Installation

Install the latest release from PyPI:

```bash
python3 -m pip install -U cleanvid
```

Or install directly from GitHub:

```bash
python3 -m pip install -U 'git+https://github.com/mmguero/cleanvid'
```

---

## 🔧 Prerequisites

cleanvid requires:

- Python 3
- [FFmpeg](https://www.ffmpeg.org)
- [babelfish](https://github.com/Diaoul/babelfish)
- [delegator.py](https://github.com/kennethreitz/delegator.py)
- [pysrt](https://github.com/byroot/pysrt)
- [subliminal](https://github.com/Diaoul/subliminal)

Install FFmpeg via your OS package manager or from [ffmpeg.org](https://www.ffmpeg.org/download.html). Python dependencies are installed automatically via `pip`.

---

## 🚀 Usage

```bash
cleanvid -i EXAMPLE.mp4 -s subs.srt -o output.mp4 --re-encode-audio
```

For full options:

```bash
cleanvid --help
```

See the full CLI reference above for all flags and modes.

---

## 🐳 Docker Support

A [Dockerfile](./docker/Dockerfile) is provided to run cleanvid in a container. GPU acceleration is supported via NVIDIA NVENC.

### 🔧 Build the Image

```bash
./docker/build_docker.sh
```

This builds a container with FFmpeg 8.0 and NVENC support.

### 🚀 Run with GPU Acceleration

To use NVIDIA GPU acceleration:

1. Install the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
2. Run with `--gpus all` and mount the required runtime libraries:

```bash
sudo docker run --rm --gpus all \
  -v "$PWD:/videos" \
  -v /usr/lib/x86_64-linux-gnu/libnvidia-encode.so.1:/usr/lib/x86_64-linux-gnu/libnvidia-encode.so.1:ro \
  -v /usr/lib/x86_64-linux-gnu/libnvcuvid.so.1:/usr/lib/x86_64-linux-gnu/libnvcuvid.so.1:ro \
  --entrypoint ffmpeg \
  oci.guero.org/cleanvid:gpu \
  -y \
  -i /videos/EXAMPLE.mp4 \
  -c:v h264_nvenc -preset fast -crf 23 \
  -an \
  /videos/output.nvenc.mp4
```

> ⚠️ This command mounts the required NVIDIA runtime libraries (`libnvidia-encode.so.1`, `libnvcuvid.so.1`) from your host into the container. Without these, FFmpeg will not be able to access NVENC encoders and will silently fall back to CPU or fail.

> ✅ You must have an NVIDIA GPU and driver version ≥ 570.0 installed on your host system.

---

### 🧪 Verify NVENC Availability

```bash
sudo docker run --rm --gpus all \
  -v /usr/lib/x86_64-linux-gnu/libnvidia-encode.so.1:/usr/lib/x86_64-linux-gnu/libnvidia-encode.so.1:ro \
  -v /usr/lib/x86_64-linux-gnu/libnvcuvid.so.1:/usr/lib/x86_64-linux-gnu/libnvcuvid.so.1:ro \
  --entrypoint ffmpeg \
  oci.guero.org/cleanvid:gpu -encoders | grep nvenc
```

You should see:
```
V....D h264_nvenc           NVIDIA NVENC H.264 encoder (codec h264)
```

---

### 🛠️ Run Interactively (for debugging)

```bash
sudo docker run --rm -it --gpus all \
  -v "$PWD:/videos" \
  -v /usr/lib/x86_64-linux-gnu/libnvidia-encode.so.1:/usr/lib/x86_64-linux-gnu/libnvidia-encode.so.1:ro \
  -v /usr/lib/x86_64-linux-gnu/libnvcuvid.so.1:/usr/lib/x86_64-linux-gnu/libnvcuvid.so.1:ro \
  --entrypoint /bin/bash \
  oci.guero.org/cleanvid:gpu
```

Then run:

```bash
cleanvid -i EXAMPLE.mp4 --re-encode-video -o output.mp4
```

---

## 🤝 Contributing

Pull requests are welcome! If you’d like to help improve cleanvid, feel free to fork and submit changes.

---

## 👤 Author

**Seth Grover** — [mmguero](https://github.com/mmguero)

---

## 📄 License

BSD 3-Clause License — see [LICENSE](LICENSE)

---

## 🙏 Acknowledgments

Thanks to:

- [FFmpeg](https://www.ffmpeg.org/about.html)
- [Mattias Wadman](https://github.com/wader) for his [static-ffmpeg](https://github.com/wader/static-ffmpeg) image
- [delegator.py](https://github.com/kennethreitz/delegator.py) by Kenneth Reitz
- [pysrt](https://github.com/byroot/pysrt) by Jean Boussier
- [subliminal](https://github.com/Diaoul/subliminal) by Antoine Bertin
