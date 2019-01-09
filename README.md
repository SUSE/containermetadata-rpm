# containerinfo-rpm

[![Build Status](https://travis-ci.com/davidcassany/containerinfo-rpm.svg?branch=master)](https://travis-ci.com/davidcassany/containerinfo-rpm)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/8cf428bba89e4e8c8cc1cb91920b861e)](https://www.codacy.com/app/davidcassany/containerinfo-rpm?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=davidcassany/containerinfo-rpm&amp;utm_campaign=Badge_Grade)

This is KIWI hook for OBS that creates a metadata package for container images.
This the created RPM only contains a single plain text file with file with all
defined image refereces for the specific image. The references are written
in JSON format.

## Usage

In order to use this hook the OBS project configuration must include this tool
in the build environment. This can be achieved with a configuration simiar to
the following:

```bash
%if "%_repository" == "container"
Type: kiwi
Repotype: rpm-md
Patterntype: none
Preinstall: containerinfo-rpm
%endif
```

## Operation example

Consider the following sources:

```xml
<?xml version="1.0" encoding="utf-8"?>

<!--
     OBS-AddTag: namespace:mytag-<VERSION>
     OBS-AddTag: alternate/namespace:myothertag-<VERSION>-<RELEASE>
-->

<image schemaversion="6.5" name="dummytest">
  <description type="system">
    <author>SUSE Containers Team</author>
    <contact>containers@suse.com</contact>
    <specification>Test dummy kiwi description file</specification>
  </description>
  <preferences>
    <type
      image="docker"
      derived_from="obsrepositories:/base#latest">
      <containerconfig name="namespace" tag="mytag"/>
    </type>
    <version>1.2.3</version>
    <packagemanager>zypper</packagemanager>
  </preferences>
  <repository>
    <source path="obsrepositories:/"/>
  </repository>
  <packages type="image">
    <package name="vim"/>
  </packages> 
</image>
```

An image being build with this sources would produce a package called
`dummytest`. This package includes a single file
`/usr/share/suse-containerinfo-images/dummytest-info` containing the following
data:

```json
{
    'namespace': ['mytag', 'mytag-1.2.3'],
    'alternate/namespace': ['myothertag-1.2.3-4.3']
}
```

Where the build release ID is `4.3`.

## Development

This is a python project that makes use of setuptools and virtual environment.

To set the development environment consider the following commands:

```bash
# Get into the repository folder
$ cd containerinfo-rpm

# Initiate the python3 virtualenv
$ python3 -m venv .env3

# Activate the virutalenv
$ source .env3/bin/activate

# Install development dependencies
$ pip install -r dev-requirements.txt

# Run tests and code style checks
$ tox
```
