
from homer.utils import remkdir, get_filepaths, copy_recursive, jpath
import homer.globals as gl
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
from enum import Enum
from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader
import sys


app = FastAPI()


class HtmlRenderObj:
    debug = True
    content = ""
    relpath = ""

    def __init__(self, content, relpath):

        if gl.verbose: print (f"creating html render obj '{relpath}'...")

        self.content = content
        self.relpath = relpath

class HomerTemplateEngine(Enum):
    JINJA2 = 1

class Homer:
    def __init__(self):
        pass

    def build(
        self, 
        src_dir="public", 
        dst_dir="build", 
        template_engine:HomerTemplateEngine=HomerTemplateEngine.JINJA2,
        context={}
    ):
        """
        Build the project.

        Args:
            src_dir (str): Source directory to read files from. Default is "public".
            dst_dir (str): Destination directory to output build files. Default is "build".
            template_engine (HomerTemplateEngine): Template engine to use. Default is JINJA2.

        """

        if not os.path.exists(src_dir):
            raise FolderNotFoundError(f"Could not find source directory '{src_dir}'")

        # create build directory
        remkdir(dst_dir)

        time_build_start = time.time() # tracks when build started

        # buffer for html file info
        html_render_obj_buf: list[HtmlRenderObj] = list()



        # <<<< walk loop start
        
        for (wroot, wdirs, wfiles) in os.walk(src_dir, topdown=True):
        
            if gl.verbose: print(f"\n=== build files ===\nroot: {wroot}\ndirs: {wdirs}\nfilenames: {wfiles}\n")

            # <<<< file loop start
            if gl.verbose: print(f"<<<< file loop start\n")
            for file in wfiles:

                # >>> MARKDOWN
                if gl.verbose: print(f"markdown...")
                if file.endswith(".md"):
                    fullpath, relpath = get_filepaths(wroot, file, src_dir)

                    # read md file to str
                    with open(fullpath, "r", encoding='utf-8') as f:
                        md_buf = f.read()

                    # convert str to html
                    html_content_buf = markdown.markdown(md_buf) # html conversion buffer

                    # prepare & add to html buffer
                    html_render_relpath = relpath.replace(".md", ".html")
                    html_render_obj_buf.append(HtmlRenderObj(html_content_buf, html_render_relpath))

                # >>> HTML
                if gl.verbose: print(f"html...")
                if file.endswith(".html"):
                    fullpath, relpath = get_filepaths(wroot, file, src_dir)

                    # read html file to str
                    with open(fullpath, "r", encoding='utf-8') as f:
                        html_content_buf= f.read()
                    
                    # prepare & add to html buffer
                    html_render_obj_buf.append(HtmlRenderObj(html_content_buf, relpath))

                # >>> JS
                if gl.verbose: print(f"js...")
                if file.endswith(".js"):
                    fullpath, relpath = get_filepaths(wroot, file, src_dir)
                    copy_recursive(fullpath, dst_dir, relpath)

                # >>> CSS
                if gl.verbose: print(f"css...")
                if file.endswith(".css"):
                    fullpath, relpath = get_filepaths(wroot, file, src_dir)
                    copy_recursive(fullpath, dst_dir, relpath)
            
            # <<<< file loop end
            if gl.verbose: print(f"\n<<<< file loop end\n")

        # <<<< walk loop end



        if gl.verbose: print(f"HTML files to render (amount): {len(html_render_obj_buf)}")

        if gl.verbose:
            if template_engine == HomerTemplateEngine.JINJA2: 
                print(f"Template engine: Jinja2")

        # compile .html templates
        if template_engine == HomerTemplateEngine.JINJA2:

            # JINJA2

            template_dir = src_dir + '/templates'

            if gl.verbose: print(f"Template directory: {template_dir}")

            if not os.path.exists(template_dir):
                os.makedirs(template_dir)
            
            jinja_env = Environment(
                loader=FileSystemLoader(src_dir),
                autoescape=select_autoescape()
            )

            for obj in html_render_obj_buf:
                template = jinja_env.from_string(obj.content)
                rendered_content = template.render(context)

                if gl.verbose: print(f"Compiled template: {obj.relpath}")

                obj.content = rendered_content
                

        # write all html
        for obj in html_render_obj_buf:

            # dst path
            write_path = os.path.join(dst_dir, obj.relpath)

            # create subfolders if not exist
            os.makedirs(os.path.dirname(write_path), exist_ok=True)

            # write file to dst path
            with open(write_path, 'w') as file:
                file.write(obj.content)

            if gl.verbose: print(f"HTML written to '{obj.relpath}'")

        time_build_end = time.time()

        print(f"\n=== BUILD SUCCESSFUL ===\nTook {time_build_end - time_build_start}s to build\n")

    def run(
        self, 
        host="127.0.0.1", 
        port=8000, 
        run_dir="build"
    ):
        print("Running app...")

        # note: html has to request /static/
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

            if gl.verbose: print(f"GET - Request path: '{full_path}' -> '{safepath}'")

            # ignore
            if safepath == 'favicon.ico' or safepath.startswith("templates"):
                raise HTTPException(status_code=404, detail="Page not found")

            # root index
            if safepath == '':
                return FileResponse(jpath(run_dir, "index.html"), media_type="text/html")
            
            # subfolder index
            att_idx_path = jpath(run_dir, safepath, "index.html")
            print(f"GET - Attempting index path '{att_idx_path}'")
            if att_idx_path.exists():
                # subfolder index
                return FileResponse(att_idx_path)
            else:
                # subfolder file

                att_filepath = jpath(run_dir, safepath)
                att_filepath_html = att_filepath.with_suffix(".html")

                print(f"GET - Attempting file '{att_filepath_html}'")

                if att_filepath_html.exists():
                    return FileResponse(att_filepath_html)
                else:
                    raise HTTPException(status_code=404, detail="Page not found")

        # run app
        if gl.verbose: print(f"Starting API with uvicorn...")

        uvicorn.run(app, host=host, port=port)
