from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


def validate_index_names(index_names, search_version=1):
    for i in index_names:
        if i not in settings.SEARCH_INDICES or \
                search_version not in settings.SEARCH_INDICES[i]['compat_search_versions']:
            raise ValidationError(_('\'{}\' is not a valid index.'.format(i)))
