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


from django.shortcuts import render
from django.utils.translation import gettext as _


def _exc_message(exception, default_message):
    if exception and exception.args and isinstance(exception.args[0], str):
        return exception.args[0]
    return default_message


def not_found(request, exception=None):
    return render(request, 'http_error.html', dict(
        error=_('404 – Not Found'),
        title=_('Quo vadis?'),
        message=_exc_message(exception, _('The requested URL could not be found on the server.'))
    ), status=404)


def server_error(request, exception=None):
    return render(request, 'http_error.html', dict(
        error=_('500 – Internal Server Error'),
        title=_('Oops! This shouldn\'t happen!'),
        message=_exc_message(exception, _('We experienced an internal error. Our server kittens have been '
                                          'notified and they are working hard to fix it. Please try again later.'))
    ), status=500)


def permission_denied(request, exception=None):
    return render(request, 'http_error.html', dict(
        error=_('403 – Forbidden'),
        title=_('Not so fast!'),
        message=_exc_message(exception, _('You are not allowed to access this URL.'))
    ), status=403)


def bad_request(request, exception=None):
    return render(request, 'http_error.html', dict(
        error=_('400 – Bad Request'),
        title=_('What did you say?'),
        message=_exc_message(exception, _('Sorry, we couldn\'t understand your request.'))
    ), status=400)
