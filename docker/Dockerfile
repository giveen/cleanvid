# Use NVIDIA's runtime-compatible base image
FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

LABEL maintainer="mero.mero.guero@gmail.com"
LABEL org.opencontainers.image.title="oci.guero.org/cleanvid"
LABEL org.opencontainers.image.description="Containerized cleanvid with GPU support"

ENV PYTHONUNBUFFERED=1

# Install build dependencies
RUN apt-get update && apt-get install -y \
    python3-pip python3-setuptools python3-wheel \
    git build-essential pkg-config \
    libx264-dev libx265-dev libvpx-dev libfdk-aac-dev libmp3lame-dev libopus-dev \
    libass-dev libfreetype6-dev libfontconfig1-dev \
    yasm nasm wget

# Install NVENC headers
RUN git clone https://git.videolan.org/git/ffmpeg/nv-codec-headers.git && \
    cd nv-codec-headers && \
    make && \
    make install && \
    ldconfig

# Build FFmpeg 8.0 with NVENC support
RUN git clone https://git.ffmpeg.org/ffmpeg.git /ffmpeg && \
    cd /ffmpeg && \
    git checkout release/8.0 && \
    ./configure \
      --enable-nonfree \
      --enable-gpl \
      --enable-libx264 \
      --enable-libx265 \
      --enable-libvpx \
      --enable-libfdk-aac \
      --enable-libmp3lame \
      --enable-libopus \
      --enable-libass \
      --enable-libfreetype \
      --enable-nvenc \
      --enable-shared && \
    make -j$(nproc) && \
    make install && \
    ldconfig

# Install cleanvid
ADD . /usr/local/src/cleanvid
RUN python3 -m pip install /usr/local/src/cleanvid && \
    rm -rf /usr/local/src/cleanvid

# Inject NVIDIA runtime libraries for NVENC support
COPY libnvidia-encode.so.1 /usr/lib/x86_64-linux-gnu/
COPY libnvcuvid.so.1 /usr/lib/x86_64-linux-gnu/
RUN ldconfig

ENTRYPOINT ["cleanvid"]
CMD []
