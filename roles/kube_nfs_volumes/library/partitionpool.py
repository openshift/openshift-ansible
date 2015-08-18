#!/usr/bin/python
"""
Ansible module for partitioning.
"""

# There is no pyparted on our Jenkins worker
# pylint: disable=import-error
import parted

DOCUMENTATION = """
---
module: partitionpool
short_description; Partition a disk into parititions.
description:
  - Creates partitions on given disk based on partition sizes and their weights.
    Unless 'force' option is set to True, it ignores already partitioned disks.

    When the disk is empty or 'force' is set to True, it always creates a new
    GPT partition table on the disk. Then it creates number of partitions, based
    on their weights.

    This module should be used when a system admin wants to split existing disk(s)
    into pools of partitions of specific sizes. It is not intended as generic disk
    partitioning module!

    Independent on 'force' parameter value and actual disk state, the task
    always fills 'partition_pool' fact with all partitions on given disks,
    together with their sizes (in bytes). E.g.:
    partition_sizes = [
        { name: sda1, Size: 1048576000 },
        { name: sda2, Size: 1048576000 },
        { name: sdb1, Size: 1048576000 },
        ...
    ]

options:
  disk:
    description:
      - Disk to partition.
  size:
    description:
      - Sizes of partitions to create and their weights. Has form of:
        <size1>[:<weigth1>][,<size2>[:<weight2>][,...]]
      - Any <size> can end with 'm' or 'M' for megabyte, 'g/G' for gigabyte
        and 't/T' for terabyte. Megabyte is used when no unit is specified.
      - If <weight> is missing, 1.0 is used.
      - From each specified partition <sizeX>, number of these partitions are
        created so they occupy spaces represented by <weightX>, proportionally to
        other weights.

      - Example 1: size=100G says, that the whole disk is split in number of 100 GiB
        partitions. On 1 TiB disk, 10 partitions will be created.

      - Example 2: size=100G:1,10G:1 says that ratio of space occupied by 100 GiB
        partitions and 10 GiB partitions is 1:1. Therefore, on 1 TiB disk, 500 GiB 
        will be split into five 100 GiB partition and 500 GiB will be split into fifty
        10GiB partitions.
      - size=100G:1,10G:1 = 5x 100 GiB and 50x 10 GiB partitions (on 1 TiB disk).

      - Example 3: size=200G:1,100G:2 says that the ratio of space occupied by 200 GiB
        partitions and 100GiB partition is 1:2. Therefore, on 1 TiB disk, 1/3
        (300 GiB) should be occupied by 200 GiB partitions. Only one fits there,
        so only one is created (we always round nr. of partitions *down*). Teh rest
        (800 GiB) is split into eight 100 GiB partitions, even though it's more
        than 2/3 of total space - free space is always allocated as much as possible.
      - size=200G:1,100G:2 = 1x 200 GiB and 8x 100 GiB partitions (on 1 TiB disk).

      - Example: size=200G:1,100G:1,50G:1 says that the ratio of space occupied by
        200 GiB, 100 GiB and 50 GiB partitions is 1:1:1. Therefore 1/3 of 1 TiB disk
        is dedicated to 200 GiB partitions. Only one fits there and only one is
        created. The rest (800 GiB) is distributed according to remaining weights:
        100 GiB vs 50 GiB is 1:1, we create four 100 GiB partitions (400 GiB in total)
        and eight 50 GiB partitions (again, 400 GiB).
      - size=200G:1,100G:1,50G:1 = 1x 200 GiB, 4x 100 GiB and 8x 50 GiB partitions
        (on 1 TiB disk).
        
  force:
    description:
      - If True, it will always overwite partition table on the disk and create new one.
      - If False (default), it won't change existing partition tables.

"""

# It's not class, it's more a simple struct with almost no functionality.
# pylint: disable=too-few-public-methods
class PartitionSpec(object):
    """ Simple class to represent required partitions."""
    def __init__(self, size, weight):
        """ Initialize the partition specifications."""
        # Size of the partitions
        self.size = size
        # Relative weight of this request
        self.weight = weight
        # Number of partitions to create, will be calculated later
        self.count = -1

    def set_count(self, count):
        """ Set count of parititions of this specification. """
        self.count = count

def assign_space(total_size, specs):
    """
    Satisfy all the PartitionSpecs according to their weight.
    In other words, calculate spec.count of all the specs.
    """
    total_weight = 0.0
    for spec in specs:
        total_weight += float(spec.weight)

    for spec in specs:
        num_blocks = int((float(spec.weight) / total_weight) * (total_size / float(spec.size)))
        spec.set_count(num_blocks)
        total_size -= num_blocks * spec.size
        total_weight -= spec.weight

def partition(diskname, specs, force=False, check_mode=False):
    """
    Create requested partitions.
    Returns nr. of created partitions or 0 when the disk was already partitioned.
    """
    count = 0

    dev = parted.getDevice(diskname)
    try:
        disk = parted.newDisk(dev)
    except parted.DiskException:
        # unrecognizable format, treat as empty disk
        disk = None

    if disk and len(disk.partitions) > 0 and not force:
        print "skipping", diskname
        return 0

    # create new partition table, wiping all existing data
    disk = parted.freshDisk(dev, 'gpt')
    # calculate nr. of partitions of each size
    assign_space(dev.getSize(), specs)
    last_megabyte = 1
    for spec in specs:
        for _ in range(spec.count):
            # create the partition
            start = parted.sizeToSectors(last_megabyte, "MiB", dev.sectorSize)
            length = parted.sizeToSectors(spec.size, "MiB", dev.sectorSize)
            geo = parted.Geometry(device=dev, start=start, length=length)
            filesystem = parted.FileSystem(type='ext4', geometry=geo)
            part = parted.Partition(
                disk=disk,
                type=parted.PARTITION_NORMAL,
                fs=filesystem,
                geometry=geo)
            disk.addPartition(partition=part, constraint=dev.optimalAlignedConstraint)
            last_megabyte += spec.size
            count += 1
    try:
        if not check_mode:
            disk.commit()
    except parted.IOException:
        # partitions have been written, but we have been unable to inform the
        # kernel of the change, probably because they are in use.
        # Ignore it and hope for the best...
        pass
    return count

def parse_spec(text):
    """ Parse string with partition specification. """
    tokens = text.split(",")
    specs = []
    for token in tokens:
        if not ":" in token:
            token += ":1"

        (sizespec, weight) = token.split(':')
        weight = float(weight) # throws exception with reasonable error string

        units = {"m": 1, "g": 1 << 10, "t": 1 << 20, "p": 1 << 30}
        unit = units.get(sizespec[-1].lower(), None)
        if not unit:
            # there is no unit specifier, it must be just the number
            size = float(sizespec)
            unit = 1
        else:
            size = float(sizespec[:-1])
        spec = PartitionSpec(int(size * unit), weight)
        specs.append(spec)
    return specs

def get_partitions(diskpath):
    """ Return array of partition names for given disk """
    dev = parted.getDevice(diskpath)
    disk = parted.newDisk(dev)
    partitions = []
    for part in disk.partitions:
        (_, _, pname) = part.path.rsplit("/")
        partitions.append({"name": pname, "size": part.getLength() * dev.sectorSize})

    return partitions


def main():
    """ Ansible module main method. """
    module = AnsibleModule(
        argument_spec=dict(
            disks=dict(required=True, type='str'),
            force=dict(required=False, default="no", type='bool'),
            sizes=dict(required=True, type='str')
        ),
        supports_check_mode=True,
    )

    disks = module.params['disks']
    force = module.params['force']
    if force is None:
        force = False
    sizes = module.params['sizes']

    try:
        specs = parse_spec(sizes)
    except ValueError, ex:
        err = "Error parsing sizes=" + sizes + ": " + str(ex)
        module.fail_json(msg=err)

    partitions = []
    changed_count = 0
    for disk in disks.split(","):
        try:
            changed_count += partition(disk, specs, force, module.check_mode)
        except Exception, ex:
            err = "Error creating partitions on " + disk + ": " + str(ex)
            raise
            #module.fail_json(msg=err)
        partitions += get_partitions(disk)

    module.exit_json(changed=(changed_count > 0), ansible_facts={"partition_pool": partitions})

# ignore pylint errors related to the module_utils import
# pylint: disable=redefined-builtin, unused-wildcard-import, wildcard-import
# import module snippets
from ansible.module_utils.basic import *
main()

