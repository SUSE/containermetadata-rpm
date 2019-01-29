# Copyright (c) 2019 SUSE Linux GmbH.  All rights reserved.
#
# This file is part of containermetadata-rpm.
#
#   containermetadata-rpm is free software: you can redistribute
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
#   along with containermetadata-rpm.  If not, see
#   <http://www.gnu.org/licenses/>.
#

import os
import subprocess
import jinja2
import shutil
import json
from kiwi.system.result import Result
from kiwi.defaults import Defaults
from lxml import etree


def main():
    """
    main-entry point for program
    """
    image = {}
    if 'TOPDIR' not in os.environ:
        image['topdir'] = '/usr/src/packages'
    image['image_dir'] = '{0}/KIWI-docker'.format(image['topdir'])
    image['bundle_dir'] = '{0}/KIWI'.format(image['topdir'])
    image['sources'] = '{0}/SOURCES'.format(image['topdir'])
    image['build_dir'] = '/usr/lib/build'

    if 'BUILD_DIST' not in os.environ:
        raise Exception('Not building inside build service')

    if not os.path.exists('{0}/kiwi.result'.format(image['image_dir'])):
        raise Exception('Kiwi result file not found')

    image['build_data'] = os.environ['BUILD_DIST'].replace('.dist', '.data')

    if not os.path.exists(image['build_data']):
        print(
            "Data file {0} not found. Skipping metadata package build".format(
                image['build_data']
            )
        )
        return

    result = Result.load('{0}/kiwi.result'.format(image['image_dir']))

    if result.xml_state.build_type.get_image() != 'docker':
        # Just leave if the image type is not docker
        return

    build_data = variable_file_parser(image['build_data'])

    image['version'] = result.xml_state.get_image_version()
    image['name'] = result.xml_state.xml_data.get_name()
    image['release'] = build_data['RELEASE']
    image['arch'] = build_data['BUILD_ARCH'].partition(':')[0]
    image['disturl'] = build_data['DISTURL']
    image['kiwi_file'] = '{0}/{1}'.format(
        image['sources'], build_data['RECIPEFILE']
    )
    image['references'] = get_image_references(
        result, image['kiwi_file'], image['version'], image['release']
    )
    image['description'] = 'Referencing metadata for {0} image'.format(
        image['name']
    )
    image['url'] = 'https://github.com/kubic-project/containermetadata-rpm'

    make_spec_from_template(image, '{0}/{1}-metadata.spec'.format(
        image['build_dir'], image['name']
    ))

    with open(
        '{0}/{1}-metadata'.format(image['sources'], image['name']), 'w'
    ) as metadata:
        json.dump(image['references'], metadata)

    rpmbuild = ['rpmbuild', '--target', image['arch'], '-ba']
    if 'disturl' in image:
        rpmbuild.extend(['--define', 'disturl {0}'.format(image['disturl'])])
    rpmbuild.append('{0}/{1}-metadata.spec'.format(
        image['build_dir'], image['name']
    ))

    run_command(rpmbuild)

    shutil.move(
        '{0}/RPMS/{1}/{2}-metadata-{3}-{4}.{1}.rpm'.format(
            image['topdir'], image['arch'], image['name'],
            image['version'], image['release']
        ),
        '{0}/OTHER'.format(image['topdir'])
    )
    shutil.move(
        '{0}/SRPMS/{1}-metadata-{2}-{3}.src.rpm'.format(
            image['topdir'], image['name'],
            image['version'], image['release']
        ),
        '{0}/OTHER'.format(image['topdir'])
    )


def get_image_references(result, kiwi_file, version, release):
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

    return add_additional_OBS_references(
        kiwi_file, version, release, references
    )


def add_additional_OBS_references(kiwi_file, version, release, references):
    addTag_comments = [
        elem.text for action, elem in etree.iterparse(
            kiwi_file, events=("comment", "start")
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


def variable_file_parser(filepath, separator="="):
    variables = {}
    with open(filepath, "r") as f:
        for line in f:
            if separator in line:
                line = line.partition(separator)
                variables[line[0]] = line[2].rstrip('\n\r').strip('\'"')
    return variables


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
    image_data, spec_file, search_path='/usr/share/containermetadata-rpm',
    template_file='spec.template'
):
    templateLoader = jinja2.FileSystemLoader(search_path)
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template(template_file)
    template.stream(image=image_data).dump(spec_file)
