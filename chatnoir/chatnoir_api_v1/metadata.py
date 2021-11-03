# Copyright 2021 Janek Bevendorff
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

from rest_framework import fields, metadata

from .serializers import OptionalListField


class ApiMetadata(metadata.SimpleMetadata):
    def get_field_info(self, field):
        """
        Given an instance of a serializer field, return a dictionary of metadata about it.
        """
        field_info = {
            'type': self.label_lookup[field]
        }
        if getattr(field, 'child', None):
            field_info['type'] = 'list of {0}'.format(self.label_lookup[field.child])

            if isinstance(field, OptionalListField):
                field_info['type'] = '{0} or list of {0}'.format(self.label_lookup[field.child])
            else:
                field_info['type'] = 'list of {0}'.format(self.label_lookup[field.child])

        for f in ('min_value', 'max_value', 'min_length', 'max_length'):
            if getattr(field, f, None) is not None:
                field_info[f] = getattr(field, f)

        if field.default is not fields.empty:
            field_info['default'] = field.default

        field_info['required'] = getattr(field, 'required', False)
        for bool_attr in ('allow_blank', 'allow_null', 'read_only'):
            if getattr(field, bool_attr, None):
                field_info[bool_attr] = True

        if getattr(field, 'help_text', None):
            field_info['desc'] = field.help_text

        return field_info
