# Copyright 2022 Janek Bevendorff
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import json
import logging.handlers
import os
import socket
import traceback

from django.utils import timezone


class LogstashFormatter(logging.Formatter):
    """
    Logging formatter for producing Logstash JSON messages.

    Structured fields can be set by using the ``extra`` log field.
    """

    def format(self, record):
        fields = {
            '@timestamp': timezone.now().isoformat().replace('+00:00', 'Z'),
            '@version': '1',
            'ecs': {'version': '8.5.2'},
            'message': record.getMessage(),
            'host': {'name': socket.gethostname()},
            'log': {
                'logger': record.name,
                'level': record.levelname,
                'origin': {
                    'file': {
                        'name': os.path.normpath(record.pathname),
                        'line': record.lineno,
                    },
                    'module': record.module,
                    'function': record.funcName,
                },
            },
            'chatnoir': {
                'settings': os.getenv('DJANGO_SETTINGS_MODULE', 'chatnoir.settings')
            }
        }

        if record.exc_info and record.exc_info[0]:
            fields['error'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'stack_trace':  ''.join(traceback.format_exception(*record.exc_info)),
            }

        if hasattr(record, 'extra'):
            fields.update(record.extra)

        return json.dumps(fields, default=str)


class LogstashTCPHandler(logging.handlers.SocketHandler):
    """
    Log messages to a Logstash server over TCP.

    Structured fields can be set by using the ``extra`` log field.
    """

    def __init__(self, host, port):
        super().__init__(host, port)
        self.formatter = LogstashFormatter()

    def makePickle(self, record):
        return self.formatter.format(record).encode() + b'\n'


class LogstashUDPHandler(logging.handlers.DatagramHandler):
    """
    Log messages to a Logstash server over UDP.

    Structured fields can be set by using the ``extra`` log field.
    """

    def __init__(self, host, port):
        super().__init__(host, port)
        self.formatter = LogstashFormatter()

    def makePickle(self, record):
        return self.formatter.format(record).encode() + b'\n'
