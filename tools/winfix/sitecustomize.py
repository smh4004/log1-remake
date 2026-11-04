"""Loaded by Python on Windows builds (tools/build_all.sh puts this folder on PYTHONPATH), so the tools behave as they do on Linux.

Text files are written with plain LF line endings, and symlinks become copies, as Windows only allows symlinks with Developer Mode on.
"""
import builtins, io, os, shutil, sys

if sys.platform == 'win32' or os.environ.get('LOG1_WINFIX_TEST'):
    _open = builtins.open

    def open_lf(file, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None):
        if 'b' not in mode and newline is None and any(c in mode for c in 'wax+'): newline = '\n'
        return _open(file, mode, buffering, encoding, errors, newline, closefd, opener)

    builtins.open = io.open = open_lf

    def copy_link(src, dst, target_is_directory=False, *, dir_fd=None):
        if not os.path.isabs(src): src = os.path.join(os.path.dirname(dst), src)
        if os.path.isdir(src): shutil.copytree(src, dst)
        else: shutil.copy2(src, dst)

    os.symlink = copy_link
