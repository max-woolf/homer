
import os
import shutil
from pathlib import Path
import homer.globals as gl


def remkdir(path: str):
    """
    1. If dir exists, delete it
    2. Create dir
    """
    if os.path.exists(path):
        if gl.verbose: print(f"removing existing build directory: /{path}/")
        shutil.rmtree(path)        
    if gl.verbose: print(f"creating new build directory: /{path}/")
    os.makedirs(path)

def get_filepaths(rootdir, file, reldir):
    """
    Returns fullpath and relative path of file
    """
    fullpath = os.path.join(rootdir, file)
    relpath = os.path.relpath(fullpath, reldir)
    if gl.verbose: print(f"{file} (path: {fullpath} || relpath: {relpath})")

    return fullpath, relpath

def copy_recursive(src, dst, rel):
    """
    Copies file recursively
    """

    # Construct destination path
    dstpath = Path(dst) / rel

    if gl.verbose: print (f"copying '{src}' -> '{dstpath}'")

    # Create subdirectories if needed
    dstpath.parent.mkdir(parents=True, exist_ok=True)

    # Copy the file
    shutil.copy2(src, dstpath)

def jpath(*args):
    return Path("/".join(str(arg).strip("/") for arg in args))


