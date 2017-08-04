#!/bin/python

import re

with open('defaults/main.yml') as f:
    lines = f.read().split("\n")

def print_rvar_table(rvar_table):
    keys = ["name", "description", "default", "required"]

    sizes = {}
    for key in keys:
        sizes[key] = len(key)

    for item in rvar_table:
        for key in item.keys():
            sizes[key] = max(sizes[key], len(item[key]))

    headers = []
    delimiters = []
    for key in keys:
        headers.append(" {}{} ".format(key, " "*(sizes[key]-len(key))))
        delimiters.append("-{}-".format("-"*(sizes[key])))
    print "|{}|".format("|".join(headers))
    print "|{}|".format("|".join(delimiters))

    # sort items by variable name
    ki_items = {}
    for item in rvar_table:
        ki_items[item["name"]] = item

    for key in sorted(ki_items):
        item = ki_items[key]
        data = []
        for key in keys:
            data.append(" {}{} ".format(item[key], " "*(sizes[key]-len(item[key]))))
        print "|{}|".format("|".join(data))

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
        "description": ""
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

        pair_start = pair_end + 1

    return annotations

rvar_table = []

last_comment = ""
for line in lines:
    if line.startswith("#:"):
        last_comment = line
        continue
    # default role variable definition
    if line.startswith("r_"):
        parts = line.split(":")
        default = parts[1].strip()

        if last_comment != "":
            annotations = parse_annotations(last_comment)
            if default == "\"{{ omit }}\"":
                default = ""

            if annotations["required"] == "false":
                annotations["required"] = ""

            rvar_table.append({
                "name": parts[0],
                "description": annotations["description"],
                "default": default,
                "required": annotations["required"],
            })
            last_comment = ""
        continue

print_rvar_table(rvar_table)
