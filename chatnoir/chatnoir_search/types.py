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

import locale


# noinspection PyPep8Naming
class serp_api_meta(property):
    """
    Property indicating a basic response metadata property.
    """
    pass


# noinspection PyPep8Naming
class serp_api_meta_extended(property):
    """
    Property indicating an extended response metadata property.

    Underscores at the end of property names will be stripped during the serialization of the SERP object,
    so this can be used for replacing fields from the standard metadata in the serialized output.
    """
    pass


# noinspection PyPep8Naming
class api_value:
    """
    API response value wrapper.
    """
    def __init__(self, value):
        self.value = value

    @property
    def type(self):
        return type(self.value)

    def __repr__(self):
        return repr(self.value)

    def __str__(self):
        return str(self.value)


# noinspection PyPep8Naming
class minimal(api_value):
    """
    Minimal API response value wrapper.
    """
    pass


# noinspection PyPep8Naming
class extended(api_value):
    """
    Extended API response value wrapper.
    """
    pass


# noinspection PyPep8Naming
class explanation(extended):
    """
    Explanation field API response value wrapper.
    """
    pass


class FieldName(str):
    """
    Language-aware index field name string.

    The string is instantiated with its base name, but can return a language-aware version of
    itself upon request with a given langauge code (e.g. ``body`` can be returned as ``body_lang_en``).
    """

    def __new__(cls, value='', i18n_aware=True, pattern='{field}_lang_{lang}'):
        """
        Initialise (potentially) i18n-aware field name.

        :param value: field name
        :param i18n_aware: whether string is language-aware
        :param pattern: field name replacement pattern
        """
        s = str.__new__(cls, value)
        s.i18n_aware = i18n_aware
        s.pattern = pattern
        return s

    def i18n(self, lang):
        """
        Return language-coded version of the field name if field is langauge-aware by
        replacing the placeholders ``{field}`` and ``{lang}`` in the field name pattern.

        :param lang: language
        :return: transformed field name
        """
        if self.i18n_aware:
            return self.pattern.format(field=self, lang=lang)
        return self


class FieldValue(FieldName):

    """
    Language-aware string field value.

    WARNING: Use this only for controlled and trusted values, not for untrusted user input!

    See :class:`FieldName` for more information.
    """

    def __new__(cls, value='', i18n_aware=False):
        """
        Initialise (potentially) i18n-aware field value.

        :param value: field value
        :param i18n_aware: whether string is language-aware
        """
        s = str.__new__(cls, value)
        s.i18n_aware = i18n_aware
        return s

    def i18n(self, lang):
        """
        Return language-coded version of the field value by replacing the placeholder
        ``{lang}`` with the target language if the field name is marked language-aware.

        :param lang: language
        :return: transformed field value
        """
        if self.i18n_aware:
            if lang not in locale.locale_alias:
                raise ValueError(f'Illegal language code: {lang}')
            return self.format(self, lang=lang)
        return self
