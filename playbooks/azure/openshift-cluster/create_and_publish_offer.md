# Create and publish offer

Note:  This document is not intended for general consumption.


This document outlines the process in which to publish an image to the cloudpartner.azure.com portal.

# Publish image

The steps to build the image are as follows:

## Step 1:

Build the Openshift image using the build_node_image.yml playbook.  Once this playbook completes it should
produce a storage blob that points to the image.  This blob exists inside of the resourcegroup named images,
storage accounts named openshiftimages, and the container named, images.

```
$ ansible-playbook build_node_image.yml
```

## Step 2:

This step performs the following work:
- generates a storage blob url
- generates a sas url for the storage container
- a cancel of any current operations on the offer will be called (in case of any updates)
- if an offer exists, the current offer will be fetched and updated
- if an offer ! exist, the offer will be created
- a publish is called on the offer

```
$ ansible-playbook  create_and_publish_offer.yml -e @publishingvars.yml
```

Example publishingvars.yml
```
openshift_azure_container: images
openshift_azure_storage_account: openshiftimages
image_name: rhel7-3.9-201805211419
openshift_azure_image_publish_emails:
- support@redhat.com
openshift_azure_templ_allowed_subscriptions:
- <subcription id1>
- <subcription id2>
```
