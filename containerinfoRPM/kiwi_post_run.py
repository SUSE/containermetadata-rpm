# Copyright (c) 2019 SUSE Linux GmbH.  All rights reserved.
#
# This file is part of containerinfo-rpm.
#
#   containerinfo-rpm is free software: you can redistribute
#   and/or modify it under the terms of the GNU General Public License
#   as published by the Free Software Foundation, either version 3 of
#   the License, or (at your option) any later version.
#
#   obs-service-replace_using_package_version is distributed in the hope
#   that it will be useful, but WITHOUT ANY WARRANTY; without even the
#   implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#   See the GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with containerinfo-rpm.  If not, see <http://www.gnu.org/licenses/>.
#

import os
import subprocess
import jinja2
import platform
import shutil
import glob
import json
from kiwi.system.result import Result
from kiwi.defaults import Defaults
from lxml import etree


def main():
    """
    main-entry point for program, expects dict with arguments from docopt()
    """
    image = dict()
    if 'TOPDIR' not in os.environ:
        image['topdir'] = '/usr/src/packages'
    image['image_dir'] = '{0}/KIWI-docker'.format(image['topdir'])
    image['bundle_dir'] = '{0}/KIWI'.format(image['topdir'])
    image['sources'] = '{0}/SOURCES'.format(image['topdir'])
    image['build_dir'] = '/usr/lib/build'
    image['arch'] = platform.machine()

    image['url'] = 'FIXME'

    result = Result.load('{0}/kiwi.result'.format(image['image_dir']))

    if result.xml_state.build_type.get_image() != 'docker':
        # Just leave if the image type is not docker
        return

    image['version'] = result.xml_state.get_image_version()
    image['name'] = result.xml_state.xml_data.get_name()
    image['release'] = get_image_release(
        image['bundle_dir'], image['name'], image['version']
    )
    image['references'] = get_image_references(
        result, image['sources'], image['version'], image['release']
    )
    image['description'] = 'Referencing metadata for {0} image'.format(
        image['name']
    )

    make_spec_from_template(image, '{0}/{1}-info.spec'.format(
        image['build_dir'], image['name']
    ))

    with open(
        '{0}/{1}-info'.format(image['sources'], image['name']), 'w'
    ) as metadata:
        json.dump(image['references'], metadata)

    run_command([
        'rpmbuild', '--target', image['arch'],
        '-ba', '{0}/{1}-info.spec'.format(image['build_dir'], image['name'])
    ])

    shutil.move(
        '{0}/RPMS/{1}/{2}-{3}-{4}.{1}.rpm'.format(
            image['topdir'], image['arch'], image['name'],
            image['version'], image['release']
        ),
        '{0}/OTHER'.format(image['topdir'])
    )
    shutil.move(
        '{0}/SRPMS/{1}-{2}-{3}.src.rpm'.format(
            image['topdir'], image['name'],
            image['version'], image['release']
        ),
        '{0}/OTHER'.format(image['topdir'])
    )


def get_image_references(result, src_dir, version, release):
    references = {}
    config = result.xml_state.get_container_config()

    if 'container_name' not in config:
        config['container_name'] = Defaults.get_default_container_name()
        config['container_tag'] = Defaults.get_default_container_tag()
    if 'container_tag' not in config:
        config['container_tag'] = Defaults.get_default_container_tag()

    references[config['container_name']] = [config['container_tag']]

    if 'additional_tags' in config:
        references[config['container_name']].extend(config['additional_tags'])

    return add_additional_OBS_references(src_dir, version, release, references)


def add_additional_OBS_references(src_dir, version, release, references):
    config_file = '{0}/config.xml'.format(src_dir)
    if not os.path.exists(config_file):
        lst = glob.glob('{0}/*.kiwi')
        if not lst:
            raise Exception('KIWI description file not found')
        config_file = lst[0]
    addTag_comments = [
        elem.text for action, elem in etree.iterparse(
            config_file, events=("comment", "start")
        ) if action == 'comment' and 'OBS-AddTag:' in elem.text
    ]
    for entry in [
        line for cmt in addTag_comments
            for line in cmt.splitlines() if 'OBS-AddTag:' in line
    ]:
        for ref in entry.partition('OBS-AddTag:')[2].split():
            part = ref.partition(':')
            tag = part[2].replace(
                '<RELEASE>', release
            ).replace('<VERSION>', version)
            rep = part[0].replace(
                '<RELEASE>', release
            ).replace('<VERSION>', version)
            if rep not in references:
                references[rep] = [tag]
            else:
                references[rep].append(tag)

    return references


def get_bundled_image_file(image_name, bundle_dir):
    image_file = [
        f for f in glob.glob('{0}/{1}*docker.tar*'.format(
            bundle_dir, image_name
        )) if not f.endswith('sha256')
    ]
    if not image_file:
        raise Exception('Could not find the bundled image')
    return image_file[0]


def get_image_release(bundle_dir, img_name, img_version):
    bundle_file = get_bundled_image_file(img_name, bundle_dir)
    meta_part = bundle_file.partition(img_name)[2].partition('.docker.tar')[0]
    version_part = meta_part.partition(img_version)
    if not version_part[1]:
        raise Exception('Version not found in image name')
    release = version_part[2].partition('Build')[2]

    if not release:
        release = '0'

    return release


def run_command(command):
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ
    )
    output, error = process.communicate()
    if process.returncode != 0:
        if not error:
            error = bytes(b'(no output on stderr)')
        if not output:
            output = bytes(b'(no output on stdout)')
        raise Exception((
            'Command "{0}" failed\n\tstdout: {1}\n'
            '\tstderr: {2}'
        ).format(' '.join(command), output.decode(), error.decode()))
    return output.decode()


def make_spec_from_template(
    image_data, spec_file, search_path='/usr/share/containerinfo-rpm',
    template_file='spec.template'
):
    templateLoader = jinja2.FileSystemLoader(search_path)
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template(template_file)
    template.stream(image=image_data).dump(spec_file)
