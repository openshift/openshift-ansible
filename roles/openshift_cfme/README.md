# CloudForms Availability

As noted in [Limitations - Product Choice](#product-choice),
CloudForms 4.6 is not yet released. Until such time, this role is
limited to installing ManageIQ, the open source project that CFME is
based on.

# Table of Contents

   * [Introduction](#introduction)
   * [Requirements](#requirements)
   * [Role Variables](#role-variables)
   * [Getting Started](#getting-started)
      * [All Defaults](#all-defaults)
      * [External NFS Storage](#external-nfs-storage)
      * [Override PV sizes](#override-pv-sizes)
      * [Override Memory Requirements](#override-memory-requirements)
      * [External PostgreSQL Database](#external-postgresql-database)
   * [Limitations](#limitations)
      * [Product Choice](#product-choice)
      * [Storage](#storage)
      * [Database](#database)
   * [Configuration](#configuration)
      * [Configuration - Storage Classes](#configuration---storage-classes)
         * [NFS (Default)](#nfs-default)
         * [NFS External](#nfs-external)
         * [Cloud Provider](#cloud-provider)
         * [Preconfigured (Expert Configuration Only)](#preconfigured-expert-configuration-only)
      * [Configuration - Database](#configuration---database)
         * [Podified Database](#podified-database)
         * [External Database](#external-database)
   * [Customization](#customization)
   * [Additional Information](#additional-information)

# Introduction

This role will allow a user to install CFME 4.6 or ManageIQ on an OCP
3.7 cluster. The role provides customization options for overriding
default deployment parameters. The role includes several choices for
storage classes.

This role includes the following storage class options

* NFS - **Default** - local, on cluster
* NFS External - NFS somewhere else, like a storage appliance
* Cloud Provider - Use automatic storage provisioning from your cloud
  provider (`gce` or `aws`)
* Preconfigured - **expert only**, assumes you created everything ahead
  of time

This role allows you to host the required PostgreSQL database podified
(on a pod in the cluster) or externally (on an existing PostgreSQL
host).

You may skip ahead to the [Getting Started](#getting-started) section
now for examples of how to set up your Ansible inventory for various
deployment configurations. However, you are **strongly urged** to read
through the [Configuration](#configuration) and
[Customization](#customization) sections first.

# Requirements

* OCP 3.7 must be installed **before** running this role.

The **default** requirements are listed in the table below. These can
be overridden through customization parameters (See
[Customization](#customization), below).

**Note** that the application performance will suffer, or possibly
even fail to deploy, if these requirements are not satisfied.


| Item                | Requirement   | Description                                  | Customization Parameter       |
|---------------------|---------------|----------------------------------------------|-------------------------------|
| Application Memory  | `≥ 4.0 Gi`    | Minimum required memory for the application  | `APPLICATION_MEM_REQ`         |
| Application Storage | `≥ 5.0 Gi`    | Minimum PV size required for the application | `APPLICATION_VOLUME_CAPACITY` |
| PostgreSQL Memory   | `≥ 6.0 Gi`    | Minimum required memory for the database     | `POSTGRESQL_MEM_REQ`          |
| PostgreSQL Storage  | `≥ 15.0 Gi`   | Minimum PV size required for the database    | `DATABASE_VOLUME_CAPACITY`    |
| Cluster Hosts       | `≥ 3`         | Number of hosts in your cluster              | `∅`                           |

The implications of this table are summarized below:

* You need several cluster nodes
* Your cluster nodes must have lots of memory available
* You will need several GiB's of storage available


# Role Variables



| Variable                                       | Required | Default                        | Description                         |
|------------------------------------------------|:--------:|:------------------------------:|-------------------------------------|
| `openshift_cfme_project`                       | **No**   | `openshift-cfme`               | Namespace for the installation.     |
| `openshift_cfme_project_description`           | **No**   | *CloudForms Management Engine* | Namespace/project description.      |
| **PRODUCT CHOICE**  | | | | |
| `openshift_cfme_app_template`                  | **No**   | `miq-template`                 | The project flavor to install. Choices: <ul><li>`miq-template`: ManageIQ using a podified database</li> <li> `miq-template-ext-db`: ManageIQ using an external database</li> <li>`cfme-template`: CloudForms using a podified database<sup>[1]</sup></li> <li> `cfme-template-ext-db`: CloudForms using an external database.<sup>[1]</sup></li></ul> |
| **STORAGE OPTIONS** | | | | |
| `openshift_cfme_storage_class`                 | **No**   | `nfs`                          | Storage type to use, choices: <ul><li>`nfs` - Best used for proof-of-concept installs. Will setup NFS on a cluster host (defaults to your first master in the inventory file) to back the required PVCs. The application requires a PVC and the database (which may be hosted externally) may require a second. PVC minimum required sizes are 5GiB for the MIQ application, and 15GiB for the PostgreSQL database (20GiB minimum available space on a volume/partition if used specifically for NFS purposes)</li> <li>`nfs_external` - You are using an external NFS server, such as a netapp appliance. See the [Configuration - Storage Classes](#configuration---storage-classes) section below for required information.</li> <li>`preconfigured` - This CFME role will do NOTHING to modify storage settings. This option assumes expert knowledge and that you have done everything required ahead of time.</li> <li>`cloudprovider` - You are using an OCP cloudprovider integration for your storage class. For this to work you must have already configured the required inventory parameters for your cloud provider. Ensure `openshift_cloudprovider_kind` is defined (aws or gce) and that the applicable cloudprovider parameters are provided. |
| `openshift_cfme_storage_nfs_external_hostname` | **No**   | `false`                        | If you are using an *external NFS server*, such as a netapp appliance, then you must set the hostname here. Leave the value as `false` if you are not using external NFS. <br /> *Additionally*: **External NFS REQUIRES** that you create the NFS exports that will back the application PV and optionally the database PV.
| `openshift_cfme_storage_nfs_base_dir`          | **No**   | `/exports/`                    | If you are using **External NFS** then you may set the base path to the exports location here. <br />**Local NFS Note**: You *may* also change this value if you want to change the default path used for local NFS exports. |
| `openshift_cfme_storage_nfs_local_hostname`    | **No**   | `false`                        | If you do not have an `[nfs]` group in your inventory, or want to simply manually define the local NFS host in your cluster, set this parameter to the hostname of the preferred NFS server. The server must be a part of your OCP/Origin cluster. |
| **CUSTOMIZATION OPTIONS** | | | | |
| `openshift_cfme_app_pv_size`                   | **No**   | `5Gi`                          | How large the application PV will be in Kube units (`Gi`, `Mi`, etc) <sup>[2]</sup>|
| `openshift_cfme_db_pv_size`                    | **No**   | `15Gi`                         | How large the database PV will be in Kube units <sup>[2]</sup>|
| `openshift_cfme_template_parameters`           | **No**   | `{}`                           | A dictionary of any parameters you want to override in the application/pv templates.

* <sup>[1]</sup> `cfme-template*` will be available once CFME 4.6 is released
* <sup>[2]</sup> If you override the PV sizes, read
  [Override PV Sizes](#override-pv-sizes) (below) for additional
  required parameters



# Getting Started

Below are some inventory snippets that can help you get started right
away.

Once you've settled on a configuration scheme (and you have installed
OCP 3.7) you can install CFME using this `ansible-playbook`
invocation:

```
$ ansible-playbook -v -i <YOUR_INVENTORY> playbooks/byo/openshift-cfme/config.yml
```

## All Defaults

This example is the simplest. All of the default values and choices
are used. This will result in a fully podified CFME installation. All
application components, as well as the PostgreSQL database will be
created as pods in the OCP cluster.

```ini
[OSEv3:vars]
openshift_cfme_app_template=miq-template
```

## External NFS Storage

This is as the previous example, except that instead of using local
NFS services in the cluster it will use an external NFS server (such
as a storage appliance). Note the two new parameters:

* `openshift_cfme_storage_class` - set to `nfs_external`
* `openshift_cfme_storage_nfs_external_hostname` - set to the hostname
  of the NFS server

```ini
[OSEv3:vars]
openshift_cfme_app_template=miq-template
openshift_cfme_storage_class=nfs_external
openshift_cfme_storage_nfs_external_hostname=nfs.example.com
```

If the external NFS host exports directories under a different parent
directory, such as `/exports/hosted/prod` then we would add an
additional parameter, `openshift_cfme_storage_nfs_base_dir`:

```ini
# ...
openshift_cfme_storage_nfs_base_dir=/exports/hosted/prod
```

## Override PV sizes

This example will override the PV sizes. Note that we must **also
set** template parameters in the `openshift_cfme_template_parameters`
parameter so that the application/db will be able to make claims on
created PVs without clobbering each other.

```ini
[OSEv3:vars]
openshift_cfme_app_template=miq-template
openshift_cfme_app_pv_size=10Gi
openshift_cfme_db_pv_size=25Gi
openshift_cfme_template_parameters={'APPLICATION_VOLUME_CAPACITY': '10Gi', 'DATABASE_VOLUME_CAPACITY': '25Gi'}
```

## Override Memory Requirements

In a test or proof-of-concept installation you may need to reduce the
application/database memory requirements to fit within your
capacity. Note that reducing memory limits can result in reduced
performance or a complete failure to initialize the application.

```ini
[OSEv3:vars]
openshift_cfme_app_template=miq-template
openshift_cfme_template_parameters={'APPLICATION_MEM_REQ': '3000Mi', 'POSTGRESQL_MEM_REQ': '1Gi', 'ANSIBLE_MEM_REQ': '512Mi'}
```

Here we have instructed the installer to process the application
template with the parameter `APPLICATION_MEM_REQ` set to `3000Mi`,
`POSTGRESQL_MEM_REQ` set to `1Gi`, and `ANSIBLE_MEM_REQ` set to
`512Mi`.

These parameters can be combined with the PV size override parameters
displayed in the previous example.

## External PostgreSQL Database

To use an external database you must change the
`openshift_cfme_app_template` parameter value to `miq-template-ext-db`
or `cfme-template-ext-db`.

Additionally, database connection information **must** be supplied in
the `openshift_cfme_template_parameters` customization parameter. See
[Customization - Database - External](#external-database) for more
information.

```ini
[OSEv3:vars]
openshift_cfme_app_template=miq-template-ext-db
openshift_cfme_template_parameters={'DATABASE_IP': '10.9.8.7', 'DATABASE_PASSWORD': 'r1ck&M0r7y', ... }
```

# Limitations

This release is the first OpenShift CFME release in the OCP 3.7
series. It is not complete yet.

## Product Choice

Due to staggered release dates, **CFME support is not
integrated**. Presently this role will only deploy a ManageIQ
installation. This role will be updated once CFME 4.6 is released and
this limitation note will be removed.

## Storage

While all storage classes (`nfs`, `nfs_external`, `preconfigured`, and
`cloudprovider`) are presently supported, the local `nfs` storage
class has some specific limitations:

1. Currently only verified to work if your first master is your NFS
   host
1. Overriding the base exports path is not recommended as this may
   cause configuration conflicts with other exports on your host


# Configuration

Before you can deploy CFME you must decide *how* you want to deploy
it. There are two major decisions to make:

1. Do you want an external, or a podified database?
1. Which storage class will back your PVs?

## Configuration - Storage Classes

OpenShift CFME supports several storage class options.

###  NFS (Default)

The NFS storage class is best suited for proof-of-concept and
test/demo deployments. It is also the **default** storage class for
deployments. No additional configuration is required for this choice.

### NFS External

External NFS leans on pre-configured NFS servers to provide exports
for the required PVs. For external NFS you must have:

* For CFME: a `cfme-app` and optionally a `cfme-db` (for podified database) exports
* For ManageIQ: an `miq-app` and optionally an `miq-db` (for podified database) exports

Additional configuration is required to use external NFS. The
`openshift_cfme_storage_nfs_external_hostname` parameter must be set
to the hostname or IP of your external NFS server.

If `/exports` is not the parent directory to your CFME exports then
you must set the base directory via the
`openshift_cfme_storage_nfs_base_dir` parameter.

For example, if your server export is `/exports/hosted/prod/miq-app`
then you must set
`openshift_cfme_storage_nfs_base_dir=/exports/hosted/prod`.

### Cloud Provider

CFME can also use a cloud provider storage to back required PVs. For
this functionality to work you must have also configured the
`openshift_cloudprovider_kind` variable and all associated parameters
specific to your chosen cloud provider.

Using this storage class, when the application is created the required
PVs will automatically be provisioned using the configured cloud
provider storage integration.

### Preconfigured (Expert Configuration Only)

The *preconfigured* storage class implies that you know exactly what
you're doing and that all storage requirements have been taken care
ahead of time. Typically this means that you've already created the
correctly sized PVs.

## Configuration - Database

### Podified Database

Any `POSTGRES_*` or `DATABASE_*` template parameters in
[miq-template.yaml](files/templates/manageiq/miq-template.yaml) or
[cfme-template.yaml](files/templates/cloudforms/cfme-template.yaml)
may be customized through the `openshift_cfme_template_parameters`
hash.

### External Database

External PostgreSQL databases require you to provide database
connection parameters. You must set the required connection keys in
the `openshift_cfme_template_parameters` parameter in your
inventory. The following keys are required:

* `DATABASE_USER`
* `DATABASE_PASSWORD`
* `DATABASE_IP`
* `DATABASE_PORT` - *note: Most PostgreSQL servers run on port `5432`*
* `DATABASE_NAME`

Your inventory would contain a line similar to this:

```ini
[OSEv3:vars]
openshift_cfme_app_template=miq-template-ext-db
openshift_cfme_template_parameters={'DATABASE_IP': '10.9.8.7', 'DATABASE_PASSWORD': 'r1ck&M0r7y', ...}
```

**Note** the new value for the `openshift_cfme_app_template`
parameter, `miq-template-ext-db`.

# Customization

Application and database parameters may be customized by means of the
`openshift_cfme_template_parameters` inventory parameter.

**For example**, if you wanted to reduce the memory requirement of the
PostgreSQL pod then you could configure the parameter like this:

`openshift_cfme_template_parameters={'POSTGRESQL_MEM_REQ': '1Gi'}`

When the CFME template is processed `1Gi` will be used for the value
of the `POSTGRESQL_MEM_REQ` template parameter.

Any parameter in the `parameters` section of the
[miq-template.yaml](files/templates/manageiq/miq-template.yaml) or
[miq-template-ext-db.yaml](files/templates/manageiq/miq-template-ext-db.yaml)
may be overridden through the `openshift_cfme_template_parameters`
hash. This applies to **CloudForms** installations as well:
[cfme-template.yaml](files/templates/cloudforms/cfme-template.yaml),
[cfme-template-ext-db.yaml](files/templates/cloudforms/cfme-template-ext-db.yaml).


# Additional Information

The upstream project,
[@manageiq/manageiq-pods](https://github.com/ManageIQ/manageiq-pods),
contains a wealth of additional information useful for managing and
operating your CFME installation. Topics include:

* [Verifying Successful Installation](https://github.com/ManageIQ/manageiq-pods#verifying-the-setup-was-successful)
* [Disabling Image Change Triggers](https://github.com/ManageIQ/manageiq-pods#disable-image-change-triggers)
* [Scaling CFME](https://github.com/ManageIQ/manageiq-pods#scale-miq)
* [Backing up and Restoring the DB](https://github.com/ManageIQ/manageiq-pods#backup-and-restore-of-the-miq-database)
* [Troubleshooting](https://github.com/ManageIQ/manageiq-pods#troubleshooting)
