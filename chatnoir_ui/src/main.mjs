/*
 * Copyright 2021 Janek Bevendorff
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

import { createApp } from 'vue'
import InlineSvg from 'vue-inline-svg'
import ChatNoirApp from '@/ChatNoir.vue'
import router from '@/routes.mjs'
import xhr from '@/xhr.mjs'

import '@/assets/css/index.css'

// Running the dev server: We first need to retrieve CSRF token from backend server.
if (import.meta.env.DEV
    && import.meta.url.indexOf(import.meta.env.VITE_BACKEND_ADDRESS) !== 0
    && window._APP_SETTINGS === undefined) {
    window._APP_SETTINGS = (await xhr.default({
        method: 'GET',
        url: import.meta.env.VITE_BACKEND_ADDRESS + '?init-dev',
        withCredentials: true,
    }).catch((e) => {
        throw new Error('Failed to initialize app state. Is the backend running?\nError: ' + e)
    })).data
}

createApp(ChatNoirApp)
    .use(router)
    .component('InlineSvg', InlineSvg)
    .mount('#app')
