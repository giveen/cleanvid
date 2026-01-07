"""FFmpeg runner utilities.

This module provides a small wrapper around subprocess calls used to invoke
ffmpeg/ffprobe. It currently preserves the simple synchronous behavior used
by the rest of the codebase but centralizes command execution so it can be
enhanced later (progress parsing, streaming, cancellation, retries).
"""
import subprocess
import os


def run_cmd(cmd_list, capture_output=True, check=False, text=True, timeout=None, progress_callback=None):
    """Run a command and return an object with attributes: return_code, out, err.

    If `progress_callback` is provided and the command is an `ffmpeg` invocation,
    the runner will add `-progress pipe:1` and stream stdout, calling the
    callback with a dict of parsed key/value pairs as they arrive.
    """
    class R:
        pass

    # Debug: record invocation when requested
    try:
        if os.environ.get('CLEANVID_DEBUG_PROGRESS') == '1':
            try:
                with open('/tmp/cleanvid_ffmpeg_invocations.log', 'a') as _inv:
                    _inv.write(f"CALL: progress_cb={'Y' if progress_callback else 'N'} cmd={' '.join(cmd_list)}\n")
            except Exception:
                pass
    except Exception:
        pass

    # If a progress callback is requested and this looks like an ffmpeg call,
    # run in streaming mode and parse 'key=value' progress lines.
    if progress_callback and cmd_list and 'ffmpeg' in os.path.basename(cmd_list[0]):
        # ensure -progress pipe:1 isn't already present
        if '-progress' not in cmd_list:
            cmd_list = cmd_list[:] + ['-progress', 'pipe:1']
        try:
            proc = subprocess.Popen(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=text)
        except Exception as e:
            r = R()
            r.return_code = 1
            r.out = ''
            r.err = str(e)
            return r

        buffer = ''
        current = {}
        all_output = []
        try:
            for line in proc.stdout:
                if not line:
                    continue
                all_output.append(line)
                # optional raw ffmpeg debug logging
                try:
                    if os.environ.get('CLEANVID_DEBUG_PROGRESS') == '1':
                        with open('/tmp/cleanvid_ffmpeg_raw.log', 'a') as _rawf:
                            _rawf.write(line)
                except Exception:
                    pass
                line = line.strip()
                if '=' in line:
                    k, v = line.split('=', 1)
                    current[k.strip()] = v.strip()
                # when ffmpeg emits 'progress=...' we should flush the current block
                if line.startswith('progress='):
                    try:
                        # optional write of parsed progress block for debugging
                        if os.environ.get('CLEANVID_DEBUG_PROGRESS') == '1':
                            try:
                                with open('/tmp/cleanvid_progress.log', 'a') as _pf:
                                    _pf.write(repr(dict(current)) + "\n")
                            except Exception:
                                pass
                        progress_callback(dict(current))
                    except Exception:
                        pass
                    current.clear()
            proc.wait()
            r = R()
            r.return_code = proc.returncode
            r.out = ''.join(all_output)
            r.err = ''
            return r
        except Exception as e:
            try:
                proc.kill()
            except Exception:
                pass
            r = R()
            r.return_code = 1
            r.out = ''.join(all_output)
            r.err = str(e)
            return r

    # Fallback: simple blocking run
    try:
        p = subprocess.run(cmd_list, stdout=subprocess.PIPE if capture_output else None, stderr=subprocess.PIPE if capture_output else None, check=check, text=text, timeout=timeout)
        r = R()
        r.return_code = p.returncode
        r.out = p.stdout if capture_output else ''
        r.err = p.stderr if capture_output else ''
        # Debug: log raw output for blocking runs when requested
        try:
            if os.environ.get('CLEANVID_DEBUG_PROGRESS') == '1' and capture_output:
                try:
                    with open('/tmp/cleanvid_ffmpeg_raw.log', 'a') as _rawf:
                        if p.stdout:
                            _rawf.write(p.stdout)
                        if p.stderr:
                            _rawf.write('\nSTDERR:\n')
                            _rawf.write(p.stderr)
                except Exception:
                    pass
        except Exception:
            pass
        return r
    except Exception as e:
        r = R()
        r.return_code = 1
        r.out = ''
        r.err = str(e)
        try:
            if os.environ.get('CLEANVID_DEBUG_PROGRESS') == '1':
                try:
                    with open('/tmp/cleanvid_ffmpeg_invocations.log', 'a') as _inv:
                        _inv.write(f"ERROR: {str(e)}\n")
                except Exception:
                    pass
        except Exception:
            pass
        return r
