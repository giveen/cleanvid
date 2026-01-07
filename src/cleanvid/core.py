"""Core orchestration for CleanVid.
This module exposes a function `run_cleanvid(cleaner_cls, args)` which runs the
processing using the provided `cleaner_cls` (typically the VidCleaner class).

Keeping orchestration here keeps CLI parsing separate from processing logic.
"""
from datetime import datetime
import os
import json
import re

def run_cleanvid(cleaner_cls, args):
    """Run the cleaning process using the provided cleaner class and argparse args."""
    inFile = args.input
    outFile = args.output
    subsFile = args.subs
    lang = args.lang
    plexFile = args.plexAutoSkipJson
    if inFile:
        inFileParts = os.path.splitext(inFile)
        if not outFile:
            outFile = inFileParts[0] + "_clean" + inFileParts[1]
        if not subsFile:
            # Let the cleaner handle subtitle extraction/download if needed by passing None
            subsFile = None
        if args.plexAutoSkipId and not plexFile:
            plexFile = inFileParts[0] + "_PlexAutoSkip_clean.json"

    if plexFile and not args.plexAutoSkipId:
        raise ValueError(
            'Content ID must be specified if creating a PlexAutoSkip JSON file (https://github.com/mdhiggins/PlexAutoSkip/wiki/Identifiers)'
        )

    vParams = args.vParams
    # GPU selection left to caller; keep existing behavior
    cleaner = cleaner_cls(
        inFile,
        subsFile,
        outFile,
        args.subsOut,
        args.swears,
        args.pad,
        args.embedSubs,
        args.fullSubs,
        args.subsOnly,
        args.edl,
        args.json,
        lang,
        args.reEncodeVideo,
        args.reEncodeAudio,
        args.hardCode,
        vParams,
        args.audioStreamIdx,
        args.aParams,
        args.aDownmix,
        args.threadsInput if args.threadsInput is not None else args.threads,
        args.threadsEncoding if args.threadsEncoding is not None else args.threads,
        plexFile,
        args.plexAutoSkipId,
        args.muteAudioIndex,
    )
    cleaner.CreateCleanSubAndMuteList()
    cleaner.MultiplexCleanVideo()
