#
# Homer
#
#   a minimalist ssg framework for generating personal wikis and archiving your manuscripts
#
#
# Features:
#
# - file-based routing
# - auto markdown-to-html builds
# - minimalist templating
# - no js by default

# ==================================

import click
import os
import shutil
import markdown
import time
import typing
from pathlib import Path

verbose = True

def remkdir(path: str):
    """
    1. If dir exists, delete it
    2. Create dir
    """
    if os.path.exists(path):
        if verbose: print(f"removing existing build directory: /{path}/")
        shutil.rmtree(path)        
    if verbose: print(f"creating new build directory: /{path}/")
    os.makedirs(path)

def get_filepaths(rootdir, file, reldir):
    """
    Returns fullpath and relative path of file
    """
    fullpath = os.path.join(rootdir, file)
    relpath = os.path.relpath(fullpath, reldir)
    if verbose: print(f"{file} (path: {fullpath} / relpath: {relpath})")

    return fullpath, relpath

def copy_recursive(src, dst, rel):
    """
    Copies file recursively
    """

    # Construct destination path
    dstpath = Path(dst) / rel

    if verbose: print (f"copying '{src}' -> '{dstpath}'")

    # Create subdirectories if needed
    dstpath.parent.mkdir(parents=True, exist_ok=True)

    # Copy the file
    shutil.copy2(src, dstpath)


class HtmlRenderObj:
    debug = True

    def __init__(self, content, relpath):

        if verbose: print (f"creating html render obj '{relpath}'...")

        self.content = content
        self.relpath = relpath

class Homer:
    mounted_dir = ""
    build_dir = "build"

    def __init__(self):
        pass

    def mount(self, dirpath):
        """Mount a directory"""
        if verbose: print(f"mounting directory '{dirpath}'...")
        self.mounted_dir = dirpath

    def build(self):
        """

        Build project

        The "run" process is separate from the build

        md -> templated html -> compiled html

        """

        # create build directory
        remkdir(self.build_dir)

        time_build_start = time.time() # tracks when build started

        # buffer for html file info
        html_render_obj_buf: list[HtmlRenderObj] = list()

        # <<<< walk loop start
        for (wroot, wdirs, wfiles) in os.walk(self.mounted_dir, topdown=True):
        
            if verbose: print(f"\n=== build files ===\nroot: {wroot}\ndirs: {wdirs}\nfilenames: {wfiles}\n")

            # <<<< file loop start
            if verbose: print(f"<<<< file loop start\n")
            for file in wfiles:

                # >>> MARKDOWN
                if verbose: print(f"markdown...")
                if file.endswith(".md"):
                    fullpath, relpath = get_filepaths(wroot, file, self.mounted_dir)

                    # read md file to str
                    with open(fullpath, "r", encoding='utf-8') as f:
                        md_buf = f.read()

                    # convert str to html
                    html_content_buf = markdown.markdown(md_buf) # html conversion buffer

                    # prepare & add to html buffer
                    html_render_relpath = relpath.replace(".md", ".html")
                    html_render_obj_buf.append(HtmlRenderObj(html_content_buf, html_render_relpath))

                # >>> HTML
                if verbose: print(f"html...")
                if file.endswith(".html"):
                    fullpath, relpath = get_filepaths(wroot, file, self.mounted_dir)

                    # read html file to str
                    with open(fullpath, "r", encoding='utf-8') as f:
                        html_content_buf= f.read()
                    
                    # prepare & add to html buffer
                    html_render_obj_buf.append(HtmlRenderObj(html_content_buf, relpath))

                # >>> JS
                if verbose: print(f"js...")
                if file.endswith(".js"):
                    fullpath, relpath = get_filepaths(wroot, file, self.mounted_dir)
                    copy_recursive(fullpath, self.build_dir, relpath)

                # >>> CSS
                if verbose: print(f"css...")
                if file.endswith(".css"):
                    fullpath, relpath = get_filepaths(wroot, file, self.mounted_dir)
                    copy_recursive(fullpath, self.build_dir, relpath)
            
            # <<<< file loop end
            if verbose: print(f"\n<<<< file loop end\n")

        # <<<< walk loop end

        if verbose: print(f"HTML files to render (amount): {len(html_render_obj_buf)}")

        # compile .html templates

        # move .html to build in proper routing order

        # write all html
        for obj in html_render_obj_buf:

            # Set write path inside build folder
            write_path = os.path.join(self.build_dir, obj.relpath)

            # Create subfolders if doesn't exist
            os.makedirs(os.path.dirname(write_path), exist_ok=True)

            # Write file
            with open(write_path, 'w') as file:
                file.write(obj.content)

            if verbose: print(f"HTML written to '{obj.relpath}'")

        # move css, js to build


        time_build_end = time.time()

        print(f"\n=== BUILD SUCCESSFUL ===\nTook {time_build_end - time_build_start}s to build\n")

    def run(self):
        print("run")

        # setup fastapi



homer = Homer()
homer.mount('./testdir')

# provide cli to run & build

@click.group()
def cli():
    """Homer CLI"""
    pass

@cli.command()
def dev():
    """Run in development mode"""
    click.echo("Running in development mode...")

@cli.command()
def build():
    """Build the project"""
    click.echo("Building the project...")
    homer.build()

@cli.command()
def run():
    """Run the project"""
    click.echo("Strating the project...")

if __name__ == '__main__':
    cli()
