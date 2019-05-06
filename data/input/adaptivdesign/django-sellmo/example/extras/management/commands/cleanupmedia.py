# Copyright (c) 2014, Adaptiv Design
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import os.path

from django.core.management.base import BaseCommand

from django.apps import apps
from django.db import models
from django.utils import six


class Command(BaseCommand):
    def handle(self, *args, **options):
        used_files = set()
        storages = set()

        for app_config in apps.get_app_configs():
            for model in app_config.get_models():

                file_fields = [
                    field
                    for field in model._meta.get_fields()
                    if isinstance(field, models.FileField)]

                if not file_fields:
                    continue

                storages |= set([file_field.storage for file_field in file_fields])

                file_field_names = [
                    field.name for field in file_fields
                ]

                values = model.objects.all().values_list(*file_field_names, flat=True).distinct()
                used_files |= set([val for val in values if val])

        def find_files(storage, curdir):
            try:
                subdirs, files = storage.listdir(curdir)
            except NotImplementedError:
                pass

            files = set([
                os.path.join(curdir, f) for f in files
            ])

            for subdir in subdirs:
                files |= find_files(storage, os.path.join(curdir, subdir))

            return files

        all_files = set()
        files_storage_map = dict()

        for storage in storages:
            files = find_files(storage, '')
            for f in files:
                files_storage_map[f] = storage
            all_files |= files

        unused_files = all_files - used_files

        self.stdout.write("%s total files" % len(all_files))
        self.stdout.write("%s files in use" % len(used_files))
        self.stdout.write("Found %s unused files:\n" % len(unused_files))

        for f in unused_files:
            self.stdout.write("%s" % f)

        if unused_files:
            answer = None
            while not answer or answer not in "yn":
                answer = six.moves.input("Do you wish to delete these files? [yN] ")
                if not answer:
                    answer = "n"
                    break
                else:
                    answer = answer[0].lower()
            if answer != "y":
                return

        for f in unused_files:
            storage = files_storage_map[f]
            storage.delete(f)
