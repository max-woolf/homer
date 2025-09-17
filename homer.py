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
# - templating support
# - no js by default

# ==================================

import click
import os
import shutil
import markdown
import time
import typing
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

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
    if verbose: print(f"{file} (path: {fullpath} || relpath: {relpath})")

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

def jpath(*args):
    return Path("/".join(str(arg).strip("/") for arg in args))


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
        #for obj in html_render_obj_buf:


        # write all html
        for obj in html_render_obj_buf:

            # dst path
            write_path = os.path.join(self.build_dir, obj.relpath)

            # create subfolders if not exist
            os.makedirs(os.path.dirname(write_path), exist_ok=True)

            # write file to dst path
            with open(write_path, 'w') as file:
                file.write(obj.content)

            if verbose: print(f"HTML written to '{obj.relpath}'")

        time_build_end = time.time()

        print(f"\n=== BUILD SUCCESSFUL ===\nTook {time_build_end - time_build_start}s to build\n")

    def run(self, reload=False, host="127.0.0.1", port=8000, run_dir="build"):
        print("Running app...")

        # setup fastapi
        app = FastAPI()
        app.mount("/static", StaticFiles(directory=run_dir), name="build")

        @app.get("/ping")
        async def pong():
            return {"message": "pong"}

        # file-based routing
        # (non-html files can be accessed through /static/)
        @app.get("/{full_path:path}")
        async def serve_page(full_path: str, request: Request):

            # sanitize path
            # (though fastAPI already restricts it)
            safepath = full_path.strip().replace('..', '').replace('^', '')

            if verbose: print(f"GET - Request path: '{full_path}' -> '{safepath}'")

            if safepath == 'favicon.ico':
                return

            # root index
            if safepath == '':
                return FileResponse(jpath(run_dir, "index.html"), media_type="text/html")
            
            # subfolder index
            att_idx_path = jpath(run_dir, safepath, "index.html")
            print(f"GET - Attempting index path '{att_idx_path}'")
            if att_idx_path.exists():
                return FileResponse(att_idx_path)
            
            # subfolder file
            else:
                att_filepath = jpath(run_dir, safepath)
                att_filepath_html = att_filepath.with_suffix(".html")

                print(f"GET - Attempting file '{att_filepath_html}'")

                if att_filepath_html.exists():
                    return FileResponse(att_filepath_html)
                else:
                    raise HTTPException(status_code=404, detail="Page not found")

        # run app
        if verbose: print(f"Starting API with uvicorn...")
        uvicorn.run(app, host=host, port=port, reload=reload)



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
    click.echo("Running project in development mode...")
    homer.build()
    homer.run(reload=True)

@cli.command()
def build():
    """Build the project"""
    click.echo("Building the project...")
    homer.build()

@cli.command()
def run():
    """Run the project"""
    click.echo("Running project...")
    homer.build()
    homer.run()

if __name__ == '__main__':
    cli()
