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

from functools import wraps
from time import time

from django.conf import settings
from django.views.decorators.csrf import csrf_protect, get_token
from django.middleware.csrf import rotate_token, CSRF_SESSION_KEY


def time_limited_csrf(set_header=True):
    """
    Decorator for views that force CSRF token to be invalidated after ``CSRF_MAX_TOKEN_AGE`` minutes.

    :param set_header set CSRF token header in response
    """
    def decorator(func):
        func = csrf_protect(func)
        if set_header:
            func = with_csrf_header(func)

        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if request.method not in ['HEAD', 'GET', 'OPTIONS', 'TRACE']:
                if CSRF_SESSION_KEY in request.session:
                    time_key = CSRF_SESSION_KEY + '_TIME'
                    if time_key not in request.session:
                        request.session[time_key] = time()

                    if time() - request.session[time_key] > settings.CSRF_MAX_TOKEN_AGE:
                        del request.session[CSRF_SESSION_KEY]
                        request.session[time_key] = time()
                        rotate_token(request)

            return func(request, *args, **kwargs)

        return wrapper

    return decorator


def with_csrf_header(func):
    """
    Decorator for setting the CSRF token header on a view response.
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        response = func(request, *args, **kwargs)
        response.headers[settings.CSRF_HEADER_SET_NAME] = get_token(request)
        return response
    return csrf_protect(wrapper)
