from rest_framework import fields, metadata, serializers

from .serializers import OptionalListField


class SimpleSearchMetadata(metadata.SimpleMetadata):
    def get_field_info(self, field):
        """
        Given an instance of a serializer field, return a dictionary
        of metadata about it.
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
