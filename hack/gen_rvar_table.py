#!/usr/bin/env python
from __future__ import print_function
import re
import jinja2
import optparse
import logging


def setOptions():

	parser = optparse.OptionParser("%prog ")

	parser.add_option(
	    "", "-d", "--defaults", dest="defaults", default = "",
	    help = "Location of the defaults/main.yml file"
	)

	parser.add_option(
	    "", "-t", "--table", dest="table", default = False, action="store_true",
	    help = "Generate role variable table"
	)

	parser.add_option(
	    "", "-c", "--checks", dest="checks", default = False, action="store_true",
	    help = "Generate a list of check tasks"
	)

	return parser

def checkOptions(options):

	if options.defaults == "":
		logging.error("--defaults missing")
		exit(1)

	if not options.table and not options.checks:
		logging.error("at least one of --table|--checks needs to be set")
		exit(1)

def print_rvar_table(rvar_table):
    keys = ("name", "description", "default", "required")

    sizes = {}
    for key in keys:
        sizes[key] = len(key)

    for item in rvar_table:
        for key in keys:
            sizes[key] = max(sizes[key], len(item[key]))

    headers = []
    delimiters = []
    for key in keys:
        headers.append(" " + key.ljust(sizes[key] + 1))
        delimiters.append("-"*(sizes[key] + 2))
    print("|{}|".format("|".join(headers)))
    print("|{}|".format("|".join(delimiters)))

    # sort items by variable name
    ki_items = {}
    for item in rvar_table:
        ki_items[item["name"]] = item

    for key in sorted(ki_items):
        item = ki_items[key]
        data = []
        for key in keys:
            data.append(" " + item[key].ljust(sizes[key] + 1))
        print("|{}|".format("|".join(data)))

required_template_task_str = """
- name: "Fail if {{ role_variable_name }} is not defined"
  fail:
    msg: "{{ role_variable_name }} must be specified for this role"
  when:
  - {{ role_variable_name }} is not defined
"""

required_when_template_task_str = """
- name: "Fail if {{ role_variable_name }} is not defined"
  fail:
    msg: "{{ role_variable_name }} must be specified for this role"
  when:
  - {{ role_variable_name }} is not defined
  {%- for condition in role_variable_condition %}
  - {{ condition -}}
  {% endfor %}
"""

choices_template_task_str = """
- name: Fail if invalid {{ role_variable_name }} provided
  fail:
    msg: "{{ role_variable_name }} can only be set to a single value from {{ role_variable_choices }}"
  when:
  - {{ role_variable_name }} is defined
  - {{ role_variable_name }} not in {{ role_variable_choices }}
"""

def generate_check_tasks(rvar_table):
    checks = []
    for item in rvar_table:
        if item["required"]:
            template_vars = {
                "role_variable_name": item["name"]
            }
            # cause the PyYAML will reorder the keys
            checks.append(jinja2.Environment().from_string(required_template_task_str).render(template_vars))
        if item["required_when"]:
            for conditions in item["required_when"]:
                template_vars = {
                    "role_variable_name": item["name"],
                    "role_variable_condition": conditions,
                }
                # cause the PyYAML will reorder the keys
                checks.append(jinja2.Environment().from_string(required_when_template_task_str).render(template_vars))
        if item["choices"]:
            template_vars = {
                "role_variable_name": item["name"],
                "role_name": "openshift_node",
                "role_variable_choices": item["choices"],
            }
            # cause the PyYAML will reorder the keys
            checks.append(jinja2.Environment().from_string(choices_template_task_str).render(template_vars))

    print("---" + "\n".join(checks))


def get_delims(line, skip_list=False):
    # replace all "...", '...' and [...] with # so it is easy to determine
    # position of the ',' symbol
    line = re.sub(r'("[^"]*")', lambda l: '#'*len(l.group()) , line)
    line = re.sub(r"('[^']*')", lambda l: '#'*len(l.group()) , line)
    if not skip_list:
        line = re.sub(r"(\[[^\]]*\])", lambda l: '#'*len(l.group()) , line)
    return re.findall(r"[^,]+", line)

def parse_list(value):
    value = value[1:-1]
    pair_start = 0
    items = []
    for substr in get_delims(value, skip_list=True):
        pair_end = pair_start + len(substr)
        item = value[pair_start:pair_end].strip()
        if item.startswith('"') or item.startswith("'"):
            item = item[1:-1]
        items.append(item)
        pair_start = pair_end + 1
    return items

def parse_annotations(line):
    if not line.startswith("#:"):
        return {}

    line = line[2:]

    annotations = {
        # set false to empty to make the column more transparent
        "required": "",
        "description": "",
        "default": "",
        "required_when": [],
        "choices": [],
    }

    pair_start = 0
    for substr in get_delims(line):
        pair_end = pair_start + len(substr)
        pair = line[pair_start:pair_end].split("=")
        key = pair[0].strip()
        value = "=".join(pair[1:]).strip()
        if key == "required":
            annotations["required"] = value
        elif key == "description":
            annotations["description"] = value[1:-1]
        elif key == "choices":
            annotations["choices"] = parse_list(value)
        elif key == "name":
            annotations["name"] = value
        elif key == "required_when":
            annotations["required_when"].append(parse_list(value))

        pair_start = pair_end + 1
    return annotations

if __name__ == "__main__":

    options, args = setOptions().parse_args()
    checkOptions(options)

    with open(options.defaults) as f:
        lines = f.read().split("\n")


    rvar_table = []

    annotations = {}
    for line in lines:
        if line.startswith("#:"):
            annotations = parse_annotations(line)
            if "name" in annotations:
                if annotations["required"] == "false":
                    annotations["required"] = ""

                rvar_table.append(annotations)
                annotations = {}
            continue
        # default role variable definition
        if line.startswith("r_"):
            parts = line.split(":")
            default = parts[1].strip()

            if annotations != {}:
                if annotations["required"] == "false":
                    annotations["required"] = ""

                annotations["name"] = parts[0]

                rvar_table.append(annotations)
                last_annotations = {}
            continue

    if options.table:
        print_rvar_table(rvar_table)
    elif options.checks:
        generate_check_tasks(rvar_table)
