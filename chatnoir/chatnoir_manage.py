#!/usr/bin/env python3
#
# Copyright 2025 Janek Bevendorff
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys

from django.core.management import execute_from_command_line
from django.core.management.commands import runserver

# Change default addr from 127.0.0.1 to localhost to avoid CORS issues with Vue dev server
runserver.Command.default_addr = 'localhost'

path = os.path.dirname(__file__)
if path not in sys.path:
    sys.path = [path] + sys.path


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatnoir.settings')
    execute_from_command_line(sys.argv)


def serve():
    if len(sys.argv) < 2:
        module = 'chatnoir'
    else:
        module = sys.argv[1]

    os.environ['DJANGO_SETTINGS_MODULE'] = f'{module}.settings'
    try:
        if '--help' not in sys.argv:
            execute_from_command_line([sys.argv[0], 'migrate'])
        execute_from_command_line([sys.argv[0], 'runserver', *sys.argv[2:]])
    except ModuleNotFoundError:
        print(f'No settings module found for {module}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
