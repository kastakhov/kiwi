from nose.tools import *
from mock import patch
from mock import call
import mock

from . import nose_helper

from kiwi.exceptions import *
from kiwi.boot.image.base import BootImageBase


class TestBootImageBase(object):
    @patch('kiwi.boot.image.base.mkdtemp')
    @patch('kiwi.boot.image.base.os.path.exists')
    @patch('platform.machine')
    def setup(self, mock_machine, mock_exists, mock_mkdtemp):
        mock_machine.return_value = 'x86_64'
        self.boot_xml_state = mock.Mock()
        self.xml_state = mock.Mock()
        self.xml_state.xml_data.get_name = mock.Mock(
            return_value='some-image'
        )
        self.xml_state.get_image_version = mock.Mock(
            return_value='1.2.3'
        )
        self.xml_state.build_type.get_boot = mock.Mock(
            return_value='oemboot/suse-13.2'
        )
        mock_mkdtemp.return_value = 'boot-root-directory'
        mock_exists.return_value = True
        self.boot_image = BootImageBase(
            self.xml_state, 'some-target-dir'
        )
        mock_mkdtemp.assert_called_once_with(
            prefix='boot-image.', dir='some-target-dir'
        )

    @raises(KiwiTargetDirectoryNotFound)
    def test_boot_image_raises(self):
        BootImageBase(
            self.xml_state, 'target-dir-does-not-exist', 'some-root-dir'
        )

    @raises(NotImplementedError)
    def test_prepare(self):
        self.boot_image.prepare()

    @raises(NotImplementedError)
    def test_create_initrd(self):
        self.boot_image.create_initrd()

    @patch('os.listdir')
    def test_is_prepared(self, mock_listdir):
        mock_listdir.return_value = True
        assert self.boot_image.is_prepared() == mock_listdir.return_value

    @patch('kiwi.boot.image.base.XMLState.copy_strip_sections')
    def test_import_system_description_elements(self, mock_strip):
        self.boot_image.import_system_description_elements()
        assert self.xml_state.copy_displayname.called
        assert self.xml_state.copy_name.called
        assert self.xml_state.copy_repository_sections.called
        assert self.xml_state.copy_drivers_sections.called
        assert mock_strip.called
        assert self.xml_state.copy_preferences_subsections.called
        assert self.xml_state.copy_bootincluded_packages.called
        assert self.xml_state.copy_bootincluded_archives.called
        assert self.xml_state.copy_bootdelete_packages.called
        assert self.xml_state.copy_build_type_attributes.called
        assert self.xml_state.copy_systemdisk_section.called
        assert self.xml_state.copy_machine_section.called
        assert self.xml_state.copy_oemconfig_section.called

    @patch('kiwi.defaults.Defaults.get_boot_image_description_path')
    def test_get_boot_description_directory(self, boot_path):
        boot_path.return_value = 'boot_path'
        assert self.boot_image.get_boot_description_directory() == \
            'boot_path/oemboot/suse-13.2'

    @patch('kiwi.boot.image.base.Command.run')
    @patch('os.path.exists')
    def test_destructor(self, mock_path, mock_command):
        mock_path.return_value = True
        self.boot_image.__del__()
        assert mock_command.call_args_list == [
            call(['rm', '-r', '-f', 'boot-root-directory']),
        ]
