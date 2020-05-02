from invoke import task
from shutil import which
import os,sys

@task
def clean(c, bytecode=False, extra=''):
    patterns = ['build']
    if bytecode:
        patterns.append('**/*.pyc')
    if extra:
        patterns.append(extra)
    for pattern in patterns:
        c.run("rm -rf {}".format(pattern))

@task
def build(c, update_requirements=True):
    poetry = which("poetry") is not None
    conda = which("poetry") is not None and os.path.exists(os.path.join(sys.prefix, 'conda-meta'))
    python_command = "poetry run python" if poetry else "python"

    if update_requirements:
        if conda:
            c.run("conda env export > environment.yml")
        if poetry:
            c.run("poetry export -f requirements.txt > requirements.txt")
        else: 
            c.run("pip freeze > requirements.txt")

    # Create dist files
    c.run(f"{python_command} setup.py sdist")
    c.run(f"{python_command} setup.py bdist_wheel")