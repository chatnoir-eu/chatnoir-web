/*
 * Copyright 2025 Janek Bevendorff
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import axios from "axios"

// Pre-configure Axios instance
axios.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
axios.defaults.headers.common['Content-Type'] = 'application/json';
axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-Csrf-Token';

// Dev server, first need to retrieve CSRF token from backend server
if (import.meta.env.DEV && import.meta.url.indexOf(import.meta.env.VITE_BACKEND_ADDRESS) !== 0) {
    await axios({
        method: 'GET',
        url: import.meta.env.VITE_BACKEND_ADDRESS,
        withCredentials: true,
    }).catch((e) => {
        throw new Error('Failed to retrieve CSRF token. ' + e)
    })
}

export default axios
