#!/usr/bin/env python
from __future__ import print_function

import argparse
import re
import jinja2
import logging
import json


def setOptions():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--json", dest="json", default="",
        help="Configuration generator file, e.g. generate.json"
    )

    parser.add_argument(
        "--target", dest="target", default="",
        help="File to generate to"
    )

    parser.add_argument(
        "--defaults", dest="defaults", default="",
        help="Location of the defaults/main.yml file"
    )

    parser.add_argument(
        "--table", dest="table", default=False, action="store_true",
        help="Generate role variable table"
    )

    parser.add_argument(
        "--checks", dest="checks", default=False, action="store_true",
        help="Generate a list of check tasks"
    )

    return parser


def checkOptions(options):

    if options.json == "" and options.defaults == "":
        logging.error("at least on of --json|--defaults needs to be set")
        exit(1)

    if options.defaults != "" and (not options.table and not options.checks):
        logging.error("at least one of --table|--checks needs to be set")
        exit(1)


def generate_set_fact_tasks(mapping):
    set_facts_template_str = """- set_fact:
    {{ dest_var }}: "{{ "{{" }} {{ src_var }} {{ "}}" }}"
  when: {{ src_var }} is defined
"""
    tasks = []
    for dest in mapping:
        template_vars = {
            "dest_var": dest,
            "src_var": mapping[dest]
        }
        tasks.append(jinja2.Environment().from_string(set_facts_template_str).render(template_vars))
    return tasks


def generate_check_tasks(rvar_table):
    required_template_task_str = """- name: "Fail if {{ role_variable_name }} is not defined"
  fail:
    msg: "{{ role_variable_name }} must be specified for this role"
  when:
  - {{ role_variable_name }} is not defined
"""

    required_when_template_task_str = """- name: "Fail if {{ role_variable_name }} is not defined"
  fail:
    msg: "{{ role_variable_name }} must be specified for this role"
  when:
  - {{ role_variable_name }} is not defined
  {%- for condition in role_variable_condition %}
  - {{ condition -}}
  {% endfor %}
"""

    choices_template_task_str = """- name: Fail if invalid {{ role_variable_name }} provided
  fail:
    msg: "{{ role_variable_name }} can only be set to a single value from {{ role_variable_choices }}"
  when:
  - {{ role_variable_name }} is defined
  - {{ role_variable_name }} not in {{ role_variable_choices }}
"""

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

    return checks


def get_delims(line, skip_list=False):
    # replace all "...", '...' and [...] with # so it is easy to determine
    # position of the ',' symbol
    line = re.sub(r'("[^"]*")', lambda l: '#' * len(l.group()), line)
    line = re.sub(r"('[^']*')", lambda l: '#' * len(l.group()), line)
    if not skip_list:
        line = re.sub(r"(\[[^\]]*\])", lambda l: '#' * len(l.group()), line)
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


def empty_annotation():
    return {
        # set false to empty to make the column more transparent
        "required": "",
        "description": "",
        "default": "",
        "required_when": [],
        "choices": [],
    }


def parse_annotations(line):
    if not line.startswith("#:"):
        return {}

    line = line[2:]

    annotations = empty_annotation()

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


def print_rvar_table(rvar_table):
    table_lines = []
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
        delimiters.append("-" * (sizes[key] + 2))
    table_lines.append("|{}|".format("|".join(headers)))
    table_lines.append("|{}|".format("|".join(delimiters)))

    # sort items by variable name
    ki_items = {}
    for item in rvar_table:
        ki_items[item["name"]] = item

    for key in sorted(ki_items):
        item = ki_items[key]
        data = []
        for key in keys:
            data.append(" " + item[key].ljust(sizes[key] + 1))
        table_lines.append("|{}|".format("|".join(data)))
    return "\n".join(table_lines)


def generate_tasks_file(tasks):
    return """---
# This file is automatically generate. Do not edit it manually.
{}
""".format("\n\n".join(tasks))


def generate_rvar_table(defaults_file):
    with open(defaults_file) as f:
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
            else:
                annotations = empty_annotation()

            annotations["name"] = parts[0]
            annotations["default"] = default
            rvar_table.append(annotations)
            annotations = {}

            continue

    return rvar_table


def writeTasks(tasks, target=""):
    if tasks:
        file_content = generate_tasks_file(tasks)
        if options.target == "":
            # TODO(jchaloup): check the 'target' key before the tasks are generated
            if "target" not in action:
                logging.error("unable to find 'target' key in generate.json")
                exit(1)
            with open(action["target"], "w") as f:
                f.write(file_content)
        else:
            print(file_content)


def updateREADME(readme, table):
    with open(readme, "r") as f:
        original_content = f.read()

    pattern = re.compile(r"(Role Variables[^|]*(\|[^\n]*\n)*)", re.DOTALL | re.MULTILINE)
    updated_content = pattern.sub("Role Variables\n--------------\n\n{}\n".format(table), original_content)

    with open(readme, "w") as f:
        f.write(updated_content)


if __name__ == "__main__":

    options = setOptions().parse_args()
    checkOptions(options)

    if options.json != "":

        with open(options.json) as f:
            conf = json.load(f)

        # TODO(jchaloup): verify the json file against JSON Schema
        for action in conf["actions"]:
            tasks = []
            if action["action"] == "set_fact":
                tasks = generate_set_fact_tasks(action["mapping"])
                writeTasks(tasks, options.defaults)
            elif action["action"] == "role_var_checks":
                rvar_table = generate_rvar_table(action["source"])
                tasks = generate_check_tasks(rvar_table)
                writeTasks(tasks, options.defaults)
            elif action["action"] == "role_var_table":
                rvar_table = generate_rvar_table(action["source"])
                updateREADME(action["target"], print_rvar_table(rvar_table))

    elif options.defaults:
        rvar_table = generate_rvar_table(options.defaults)
        if options.table:
            print(print_rvar_table(rvar_table))
        elif options.checks:
            tasks = generate_check_tasks(rvar_table)
            print(generate_tasks_file(tasks))
