# Copyright (c) 2015 SUSE Linux GmbH.  All rights reserved.
#
# This file is part of kiwi.
#
# kiwi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# kiwi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kiwi.  If not, see <http://www.gnu.org/licenses/>
#
import os
import platform
from tempfile import mkdtemp

# project
from ...defaults import Defaults
from ...xml_description import XMLDescription
from ...xml_state import XMLState
from ...command import Command
from ...logger import log

from ...exceptions import(
    KiwiTargetDirectoryNotFound,
    KiwiConfigFileNotFound
)


class BootImageBase(object):
    """
        Base class for boot image(initrd) task
    """
    def __init__(self, xml_state, target_dir, root_dir=None):
        self.xml_state = xml_state
        self.target_dir = target_dir
        self.initrd_filename = None
        self.temp_boot_root_directory = None
        self.boot_xml_state = None

        self.boot_root_directory = root_dir
        if not self.boot_root_directory:
            self.boot_root_directory = mkdtemp(
                prefix='boot-image.', dir=self.target_dir
            )

        if not os.path.exists(target_dir):
            raise KiwiTargetDirectoryNotFound(
                'target directory %s not found' % target_dir
            )

        self.initrd_file_name = ''.join(
            [
                self.target_dir, '/',
                self.xml_state.xml_data.get_name(),
                '.' + platform.machine(),
                '-' + self.xml_state.get_image_version(),
                '.initrd'
            ]
        )

    def prepare(self):
        """
            prepare new root system to create initrd from. Implementation
            is only needed if there is no other root system available
        """
        raise NotImplementedError

    def create_initrd(self):
        """
            implements creation of the initrd
        """
        raise NotImplementedError

    def is_prepared(self):
        return os.listdir(self.boot_root_directory)

    def load_boot_xml_description(self):
        log.info('Loading Boot XML description')
        boot_description_directory = self.get_boot_description_directory()
        boot_config_file = boot_description_directory + '/config.xml'
        if not os.path.exists(boot_config_file):
            raise KiwiConfigFileNotFound(
                'no Boot XML description found in %s' %
                boot_description_directory
            )
        boot_description = XMLDescription(
            boot_config_file
        )

        boot_image_profile = self.xml_state.build_type.get_bootprofile()
        if not boot_image_profile:
            boot_image_profile = 'default'
        boot_kernel_profile = self.xml_state.build_type.get_bootkernel()
        if not boot_kernel_profile:
            boot_kernel_profile = 'std'

        self.boot_xml_state = XMLState(
            boot_description.load(), [boot_image_profile, boot_kernel_profile]
        )
        log.info('--> loaded %s', boot_config_file)
        if self.boot_xml_state.build_type:
            log.info(
                '--> Selected build type: %s',
                self.boot_xml_state.get_build_type_name()
            )
        if self.boot_xml_state.profiles:
            log.info(
                '--> Selected boot profiles: image: %s, kernel: %s',
                boot_image_profile, boot_kernel_profile
            )

    def import_system_description_elements(self):
        self.xml_state.copy_displayname(
            self.boot_xml_state
        )
        self.xml_state.copy_name(
            self.boot_xml_state
        )
        self.xml_state.copy_repository_sections(
            target_state=self.boot_xml_state,
            wipe=True
        )
        self.xml_state.copy_drivers_sections(
            self.boot_xml_state
        )
        strip_description = XMLDescription(
            Defaults.get_boot_image_strip_file()
        )
        strip_xml_state = XMLState(strip_description.load())
        strip_xml_state.copy_strip_sections(
            self.boot_xml_state
        )
        preferences_subsection_names = [
            'bootloader_theme',
            'bootsplash_theme',
            'locale',
            'packagemanager',
            'rpm_check_signatures',
            'showlicense'
        ]
        self.xml_state.copy_preferences_subsections(
            preferences_subsection_names, self.boot_xml_state
        )
        self.xml_state.copy_bootincluded_packages(
            self.boot_xml_state
        )
        self.xml_state.copy_bootincluded_archives(
            self.boot_xml_state
        )
        self.xml_state.copy_bootdelete_packages(
            self.boot_xml_state
        )
        type_attributes = [
            'bootkernel',
            'bootloader',
            'bootprofile',
            'boottimeout',
            'btrfs_root_is_snapshot',
            'devicepersistency',
            'filesystem',
            'firmware',
            'fsmountoptions',
            'hybrid',
            'hybridpersistent',
            'hybridpersistent_filesystem',
            'installboot',
            'installprovidefailsafe',
            'kernelcmdline',
            'ramonly',
            'vga',
            'wwid_wait_timeout'
        ]
        self.xml_state.copy_build_type_attributes(
            type_attributes, self.boot_xml_state
        )
        self.xml_state.copy_systemdisk_section(
            self.boot_xml_state
        )
        self.xml_state.copy_machine_section(
            self.boot_xml_state
        )
        self.xml_state.copy_oemconfig_section(
            self.boot_xml_state
        )

    def get_boot_description_directory(self):
        boot_description = self.xml_state.build_type.get_boot()
        if boot_description:
            if not boot_description[0] == '/':
                boot_description = \
                    Defaults.get_boot_image_description_path() + '/' + \
                    boot_description
            return boot_description

    def __del__(self):
        log.info('Cleaning up %s instance', type(self).__name__)
        temp_directories = [
            self.boot_root_directory,
            self.temp_boot_root_directory
        ]
        for directory in temp_directories:
            if directory and os.path.exists(directory):
                Command.run(
                    ['rm', '-r', '-f', directory]
                )
