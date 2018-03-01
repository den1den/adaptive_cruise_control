"""
Converts *.template.dot files to images
input arguments:
- object_file
- output
"""
import os
import subprocess

import sys
from jinja2 import Environment, FileSystemLoader
import yaml

jinja2_env = Environment(
    loader=FileSystemLoader('.'),
    autoescape=False,
)


def yaml_and_template_to_dot(in_filename, template_filename, out_image_filename, object_name=None):
    assert in_filename.endswith('.yaml')
    assert template_filename.endswith('.template.dot')
    assert out_image_filename.endswith('.png')
    out_tmp_filename = template_filename[:-13] + '.tmp.dot'
    if object_name is None:
        object_name = os.path.basename(in_filename)[:-5]

    if not os.path.exists(in_filename):
        raise IOError("Could not find %s" % os.path.abspath(in_filename))
    with open(in_filename) as f:
        yaml_object = yaml.safe_load(f)
    template_to_png(template_filename, {object_name: yaml_object}, out_tmp_filename, out_image_filename)


def template_to_png(template_filename: str, kwargs, output_dot_file=None, out_image_filename=None):
    if output_dot_file is None:
        output_dot_file = template_filename.rstrip('.template.dot') + '.tmp.dot'
    template_to_dot(template_filename, kwargs, output_dot_file)
    dot_to_png(output_dot_file, out_image_filename)


def template_to_dot(template_filename, kwargs, output_dot_file=None):
    assert template_filename.endswith('.template.dot')
    if output_dot_file is None:
        output_dot_file = template_filename.rstrip('.template.dot') + '.dot'
    template = jinja2_env.get_template(template_filename)
    with open(output_dot_file, 'w+') as f:
        try:
            f.write(template.render(kwargs))
        except Exception as e:
            print("Error with %s\nobject: %s\n" % (template_filename, kwargs))
            raise e


def dot_to_png(dot_file: str, png_file=None):
    if png_file is None:
        png_file = dot_file.rstrip('.tmp.dot') + '.tmp.png'
    with open(png_file, 'w+') as img_f:
        if subprocess.call(['dot', '-T' + 'png', dot_file, '-K' + 'fdp'], stdout=img_f) != 0:
            raise Exception("Could convert to png file of %s" % dot_file)
    print("dot_to_png: %s -> %s" % (dot_file, png_file, ))


if __name__ == '__main__':
    def main():
        in_filename = sys.argv[1]
        template_filename = sys.argv[2]
        out_image_filename = sys.argv[3]
        object_name = sys.argv[4] if len(sys.argv) > 4 else None
        print("Running from %s" % os.getcwd())

        yaml_and_template_to_dot(in_filename, template_filename, out_image_filename, object_name)


    main()
