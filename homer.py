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

# store Homer data

class Homer:
    mounted_dir = ""
    build_dir = "dist"
    debug = True # debug flag

    def __init__(self):
        pass

    def mount(self, dirpath):
        """Mount a directory"""
        if self.debug: print(f"mounting directory '{dirpath}'...")
        self.mounted_dir = dirpath

    def build(self):
        """

        Build project

        The "run" process is separate from the build

        md -> templated html -> compiled html

        """

        # this should hold the tuple: (html_content, relpath)
        html_to_render = []
        for (wroot, wdirs, wfiles) in os.walk(self.mounted_dir, topdown=True):

            if self.debug: print(f"\n=== build files ===\nroot: {wroot}\ndirs: {wdirs}\nfilenames: {wfiles}\n\n")

            # file loop start

            for file in wfiles:
                if self.debug: print(f"rendering markdown files to html...")
                if file.endswith(".md"):
                    md_filepath = os.path.join(wroot, file)
                    md_relpath = os.path.relpath(md_filepath, self.mounted_dir)

                    if self.debug: print(f"\n- {file}\npath: {md_filepath}\nrelpath: {md_relpath}\n")

                    # read md file to str
                    with open(md_filepath, "r", encoding='utf-8') as f:
                        md_buf = f.read()

                    # convert str to html
                    html_conv_buf = markdown.markdown(md_buf) # html conversion buffer

                    # append to html list
                    html_to_render.append((html_conv_buf, md_relpath))
                
                if self.debug: print(f"reading html files...")
                if file.endswith(".html"):
                    html_filepath = os.path.join(wroot, file)
                    html_relpath = os.path.relpath(html_filepath, self.mounted_dir)

                    if self.debug: print(f"\n- {file}\npath: {html_filepath}\nrelpath: {html_relpath}\n")

                    # read html file to str
                    with open(html_filepath, "r", encoding='utf-8') as f:
                        html_buf = f.read()
                    
                    html_to_render.append((html_buf, html_relpath))
            
            # file loop end

        if self.debug: print(f"HTML files to render: {len(html_to_render)}")

        
                

        if os.path.exists(self.build_dir):
            if self.debug: print(f"removing existing build directory: /{self.build_dir}/")
            shutil.rmtree(self.build_dir)
        
        if self.debug: print(f"creating new build directory: /{self.build_dir}/")
        os.makedirs(self.build_dir)

        # compile .html templates

        # move .html to build in proper routing order

        # move css, js to build

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
