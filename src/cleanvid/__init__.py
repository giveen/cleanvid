"""cleanvid is a little script to mute profanity in video files."""

__version__ = "1.7.0"
__author__ = "Seth Grover <mero.mero.guero@gmail.com>"

from .cleanvid import RunCleanvid, VidCleaner, SUBTITLE_DEFAULT_LANG, VIDEO_DEFAULT_PARAMS, AUDIO_DEFAULT_PARAMS

__all__ = [
	"RunCleanvid",
	"VidCleaner",
	"SUBTITLE_DEFAULT_LANG",
	"VIDEO_DEFAULT_PARAMS",
	"AUDIO_DEFAULT_PARAMS",
]
