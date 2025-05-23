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

import { createWebHistory, createRouter } from "vue-router"

export default createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/',
            name: 'IndexSearch',
            component: () => import('@/views/IndexSearch.vue')
        },
        {
            path: '/docs/',
            name: 'Docs',
            component: () => import('@/views/Docs.vue'),
            alias: [
                '/docs/api-general',
                '/docs/api-advanced',
                '/docs/api-advanced/management',
            ]
        },
        {
            path: '/apikey/',
            name: 'ApikeyRequest',
            component: () => import('@/views/ApikeyRequest.vue'),
            children: [
                { path: 'request-academic', name: 'ApikeyRequest_Academic', component: () => import('@/views/ApikeyRequest.vue')},
                { path: 'request-passcode', name: 'ApikeyRequest_Passcode', component: () => import('@/views/ApikeyRequest.vue')},
                { path: 'request-received', name: 'ApikeyRequest_Received', component: () => import('@/views/ApikeyRequest.vue')},
                { path: 'verify/:activation_code?', name: 'ApikeyRequest_Verified', component: () => import('@/views/ApikeyRequest.vue')},
            ]
        }
    ]
})
