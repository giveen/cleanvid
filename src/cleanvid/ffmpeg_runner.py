"""FFmpeg runner utilities.

This module provides a small wrapper around subprocess calls used to invoke
ffmpeg/ffprobe. It currently preserves the simple synchronous behavior used
by the rest of the codebase but centralizes command execution so it can be
enhanced later (progress parsing, streaming, cancellation, retries).
"""
import subprocess


def run_cmd(cmd_list, capture_output=True, check=False, text=True, timeout=None):
    """Run a command and return an object with attributes: return_code, out, err.

    Kept intentionally small and compatible with the previous `_run_cmd`.
    """
    class R:
        pass

    try:
        p = subprocess.run(cmd_list, stdout=subprocess.PIPE if capture_output else None, stderr=subprocess.PIPE if capture_output else None, check=check, text=text, timeout=timeout)
        r = R()
        r.return_code = p.returncode
        r.out = p.stdout if capture_output else ''
        r.err = p.stderr if capture_output else ''
        return r
    except Exception as e:
        r = R()
        r.return_code = 1
        r.out = ''
        r.err = str(e)
        return r
