
# 🧼 cleanvid

**cleanvid** mutes profanity in video files by using subtitle-based detection and audio stream editing. It supports fast audio muting, subtitle cleaning, and hardware-accelerated video encoding (GPU) for maximum performance.

## Features
- Mute audio segments containing profanity (based on subtitles and a customizable word list)
- Create clean subtitle files with censored phrases
- Optionally embed or hardcode subtitles
- Generate EDL and PlexAutoSkip JSON files for external players
- Fast processing: copy video, re-encode audio only, or fully re-encode video
- **NEW:** Automatic GPU acceleration (`--gpu`) for NVIDIA, Intel, or AMD

---


## Installation

### Prerequisites
- Python 3.7 or newer
- FFmpeg (v6 or newer recommended)
  - Install via your OS package manager (e.g., `sudo apt install ffmpeg`) or from [ffmpeg.org](https://ffmpeg.org/download.html)


### Recommended: Use a Python virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```


### Install from source (for latest development version)
```bash
git clone https://github.com/giveen/cleanvid.git
cd cleanvid
pip install -e .
```

### Required Python packages (if installing manually)
```bash
pip install babelfish pysrt subliminal
```

### Verify installation
```bash
cleanvid --help
```

---

## Usage

### Basic Example
```bash
cleanvid -i input.mp4 -s subs.srt -o output.mp4 --re-encode-audio
```

### Fastest (audio-only mute, copy video)
```bash
cleanvid -i input.mp4 -o output.mp4 -a "-c:a aac -b:a 224k -ar 48000" -v "-c:v copy"
```

### Full re-encode (CPU)
```bash
cleanvid -i input.mp4 -o output.mp4 --re-encode-video -v "-c:v libx264 -preset fast -crf 22 -threads 8" -a "-c:a aac -b:a 224k -ar 48000"
```

### GPU acceleration (NVIDIA/Intel/AMD)
```bash
cleanvid -i input.mp4 -o output.mp4 --re-encode-video --gpu
```
This will auto-detect your GPU and select the best encoder (e.g., `h264_nvenc` for NVIDIA).

### Show all options
```bash
cleanvid --help
```

---

## Major CLI Options

- `-i`, `--input`           Input video file (required)
- `-o`, `--output`          Output video file
- `-s`, `--subs`            Subtitle file (.srt)
- `-w`, `--swears`          Profanity list file
- `-v`, `--video-params`    Custom ffmpeg video parameters
- `-a`, `--audio-params`    Custom ffmpeg audio parameters
- `--re-encode-video`       Force video re-encoding
- `--re-encode-audio`       Force audio re-encoding
- `--gpu`                   Enable GPU acceleration (auto-detects and selects best encoder)
- `--embed-subs`            Embed subtitles in output
- `--burn`                  Hardcode subtitles (implies re-encode)
- `--subs-only`             Only operate on subtitles
- `--edl`                   Generate EDL file
- `--json`                  Generate JSON file for muted segments

---

## GPU Acceleration FAQ

- **How do I enable GPU?**
  Add `--gpu` to your command. cleanvid will auto-detect NVIDIA, Intel, or AMD and select the best encoder.
- **What if I have multiple GPUs?**
  cleanvid uses the first detected GPU. For advanced control, manually set `-v "-c:v h264_nvenc"` or similar.
- **What if no GPU is found?**
  cleanvid falls back to CPU encoding (`libx264`).


---

## Docker Usage

Build the image:
```bash
./docker/build_docker.sh
```


Run in Docker:
```bash
sudo docker run --rm \
  -v "$PWD:/videos" \
  --entrypoint cleanvid \
  oci.guero.org/cleanvid:latest \
  -i /videos/input.mp4 --re-encode-video -o /videos/output.mp4
```

---

## Troubleshooting

- **ffmpeg not found:** Install ffmpeg and ensure it is in your PATH.
- **Missing Python packages:** Run `python3 -m pip install -U -r requirements.txt`.
- **GPU not detected:** Ensure drivers and runtime libraries are installed. Use `nvidia-smi` (NVIDIA), `vainfo` (Intel/AMD) to verify.

---

## License
BSD 3-Clause License — see [LICENSE](LICENSE)


---

## 🤝 Contributing

Pull requests are welcome! If you’d like to help improve cleanvid, feel free to fork and submit changes.

---

## 👤 Author

 ** Original Author ** **Seth Grover** — [mmguero](https://github.com/mmguero)
 ** Re-write Author ** ** Giveen **

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
- [FFmpeg](https://www.ffmpeg.org)
- [pysrt](https://github.com/byroot/pysrt)
- [subliminal](https://github.com/Diaoul/subliminal)
- [babelfish](https://github.com/Diaoul/babelfish)
