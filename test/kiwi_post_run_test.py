import sys
import io
from mock import patch, mock_open, call, Mock, ANY

from containermetadataRPM.kiwi_post_run import (
    get_image_references,
    main,
    run_command,
    make_spec_from_template,
    variable_file_parser
)

open_to_patch = '{0}.open'.format(
    sys.version_info.major < 3 and "__builtin__" or "builtins"
)


def test_get_image_references():
    mock_result = Mock()
    mock_result.xml_state.get_container_config.return_value = {
        'container_name': 'myname', 'container_tag': 'mytag'
    }
    mock_result.xml_state.build_type.get_image.return_value = 'docker'
    assert get_image_references(
        mock_result, 'config.xml', 'version', 'release'
    ) == {
        'myname': ['mytag'],
        'alternate/namespace': ['myothertag-version-release'],
        'namespace': ['mytag-version']
    }


def test_get_image_references_no_tag():
    mock_result = Mock()
    mock_result.xml_state.get_container_config.return_value = {
        'container_name': 'myname'
    }
    mock_result.xml_state.build_type.get_image.return_value = 'docker'
    assert get_image_references(
        mock_result, 'config.xml', '1.2.3', '4.5'
    ) == {
        'myname': ['latest'],
        'alternate/namespace': ['myothertag-1.2.3-4.5'],
        'namespace': ['mytag-1.2.3']
    }


def test_get_image_references_no_name():
    mock_result = Mock()
    mock_result.xml_state.get_container_config.return_value = {}
    mock_result.xml_state.build_type.get_image.return_value = 'docker'
    assert get_image_references(
        mock_result, 'config.xml', '12.3', '1'
    ) == {
        'kiwi-container': ['latest'],
        'alternate/namespace': ['myothertag-12.3-1'],
        'namespace': ['mytag-12.3']
    }


def test_get_image_references_additional_tags():
    mock_result = Mock()
    mock_result.xml_state.get_container_config.return_value = {
        'container_name': 'namespace', 'container_tag': 'mytag',
        'additional_tags': ['myothertag', 'anothertag']
    }
    mock_result.xml_state.build_type.get_image.return_value = 'docker'
    assert get_image_references(
        mock_result, 'config.xml', '12.3', '1'
    ) == {
        'alternate/namespace': ['myothertag-12.3-1'],
        'namespace': ['mytag', 'myothertag', 'anothertag', 'mytag-12.3']
    }


@patch('subprocess.Popen')
def test_run_command(mock_subprocess):
    mock_process = Mock()
    mock_process.communicate.return_value = (b'stdout', b'stderr')
    mock_process.returncode = 0
    mock_subprocess.return_value = mock_process
    assert run_command(['/bin/dummycmd', 'arg1']) == 'stdout'


@patch('subprocess.Popen')
def test_run_command_failure(mock_subprocess):
    mock_process = Mock()
    mock_process.communicate.return_value = (None, None)
    mock_process.returncode = 1
    mock_subprocess.return_value = mock_process
    try:
        run_command(['dummycmd', 'arg1']) == 'stdout'
    except Exception as e:
        assert 'Command "dummycmd arg1" failed' in str(e)


@patch((
    'containermetadataRPM.kiwi_post_run'
    '.jinja2.environment.TemplateStream.dump'
))
def test_make_spec_from_template(mock_dump):
    image_data = dict()
    image_data['version'] = '1.2.3'
    image_data['name'] = 'myimage'
    image_data['release'] = '3.4'
    image_data['description'] = 'Package description'
    make_spec_from_template(
        image_data, 'package.spec',
        '../containermetadataRPM', 'spec.template'
    )
    mock_dump.assert_called_once_with('package.spec')


@patch(open_to_patch)
def test_variable_file_parser(mock_open):
    mock_open.return_value = io.StringIO(u"""
RELEASE="12.3"
DISTURL='obs://someurl'
Will not be parsed
BUILD_ARCH=x86_64
    """)
    data = variable_file_parser('some_file')
    assert data == {
        'RELEASE': '12.3', 'DISTURL': 'obs://someurl', 'BUILD_ARCH': 'x86_64'
    }


def test_main_no_build_service():
    exception = False
    try:
        main()
    except Exception as e:
        exception = True
        assert 'Not building inside build service' in str(e)
    assert exception


@patch('containermetadataRPM.kiwi_post_run.os')
def test_main_no_kiwi_result(mock_os):
    mock_os.environ = {'BUILD_DIST': 'build.dist'}
    mock_os.path.exists.return_value = False
    exception = False
    try:
        main()
    except Exception as e:
        exception = True
        assert 'Kiwi result file not found' in str(e)
    assert exception


@patch('containermetadataRPM.kiwi_post_run.os')
def test_main_no_build_data(mock_os):
    mock_os.environ = {'BUILD_DIST': 'build.dist'}
    mock_os.path.exists.side_effect = lambda x: (
        False if 'build.data' == x else True
    )
    main()


@patch('containermetadataRPM.kiwi_post_run.variable_file_parser')
@patch('containermetadataRPM.kiwi_post_run.os')
@patch(open_to_patch, new_callable=mock_open)
@patch('containermetadataRPM.kiwi_post_run.etree.iterparse')
@patch('containermetadataRPM.kiwi_post_run.json.dump')
@patch('containermetadataRPM.kiwi_post_run.make_spec_from_template')
@patch('containermetadataRPM.kiwi_post_run.run_command')
@patch('containermetadataRPM.kiwi_post_run.shutil.move')
@patch('kiwi.system.result.Result.load')
def test_main(
    mock_load, mock_move, mock_command, mock_template,
    mock_dump, mock_iterparse, mock_file, mock_os, mock_parser
):
    mock_parser.return_value = {
        'RELEASE': '2.1', 'BUILD_ARCH': 'x86_64',
        'DISTURL': 'obs://someurl', 'RECIPEFILE': 'config.xml'
    }
    mock_os.environ = {'BUILD_DIST': 'build.dist'}
    mock_os.path.exists.return_value = True
    mock_result = Mock()
    mock_load.return_value = mock_result
    mock_result.xml_state.get_image_version.return_value = '1.2.3'
    mock_result.xml_state.xml_data.get_name.return_value = 'myimage'
    mock_result.xml_state.get_container_config.return_value = {
        'container_name': 'myname', 'container_tag': 'mytag'
    }
    mock_result.xml_state.build_type.get_image.return_value = 'docker'
    main()
    mock_file.assert_called_once_with(
        '/usr/src/packages/SOURCES/myimage-metadata', 'w'
    )
    mock_dump.assert_called_once_with({'myname': ['mytag']}, ANY)
    mock_command.assert_called_once_with(
        [
            'rpmbuild', '--target', 'x86_64', '-ba', '--define',
            'disturl obs://someurl', '/usr/lib/build/myimage-metadata.spec'
        ]
    )
    mock_template.assert_called_once_with(
        ANY, '/usr/lib/build/myimage-metadata.spec'
    )
    assert mock_move.call_args_list == [
        call(
            (
                '/usr/src/packages/RPMS/x86_64/'
                'myimage-metadata-1.2.3-2.1.x86_64.rpm'
            ),
            '/usr/src/packages/OTHER'
        ),
        call(
            '/usr/src/packages/SRPMS/myimage-metadata-1.2.3-2.1.src.rpm',
            '/usr/src/packages/OTHER'
        )
    ]


@patch('containermetadataRPM.kiwi_post_run.os')
@patch('kiwi.system.result.Result.load')
def test_main_no_docker_image(mock_load, mock_os):
    mock_os.environ = {'BUILD_DIST': 'build.dist'}
    mock_os.path.exists.return_value = True
    mock_result = Mock()
    mock_load.return_value = mock_result
    mock_result.xml_state.build_type.get_image.return_value = 'oci'
    main()
