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

# store Homer data

class App:
    def __init__(self, dir):
        self.dir = dir

# function to build every file in directory into static html

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

@cli.command()
def start():
    """Start the project"""
    click.echo("Strating the project...")

if __name__ == '__main__':
    cli()
