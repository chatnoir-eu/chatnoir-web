<!--
    Copyright 2021 Janek Bevendorff

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
-->

<template>
<div class="max-w-full px-5">
    <search-header ref="searchHeaderRef" v-model="searchModel" focus :progress="requestProgress" @submit="search()" />

    <div ref="resultsElement">
        <div v-if="searchModel.response && searchModel.response.hits.length" key="search-results" class="max-w-3xl mx-auto">
            <div class="flex -mb-3 text-sm">
                <div class="flex-grow">
                    Search results {{ numFormat(searchModel.response.meta.resultsFrom + 1) }}–{{ numFormat(searchModel.response.meta.resultsTo) }}
                    for <em class="font-bold">“{{ searchModel.response.meta.queryString }}”</em>
                </div>
                <div>
                    Total results: {{ numFormat(searchModel.response.meta.totalResults) }}<span v-if="searchModel.response.meta.terminatedEarly">+</span>
                    <span v-if="searchModel.response.meta.queryTime < 1500">
                        (retrieved in {{ numFormat(searchModel.response.meta.queryTime) }}&thinsp;ms)
                    </span>
                    <span v-else>
                        (retrieved in {{ numFormat(searchModel.response.meta.queryTime / 1000, { minimumFractionDigits: 1 }) }}&thinsp;s)
                    </span>
                </div>
            </div>

            <div v-for="hit in searchModel.response.hits" :key="hit.uuid">
                <component :is="SearchResult" :data="hit" :meta="searchModel.response.meta" />
            </div>
        </div>
        <div v-if="!error && searchModel.response && searchModel.response.hits.length === 0" class="max-w-3xl mt-12 mx-auto text-center text-lg">
            No results found… ;-(
        </div>
        <div v-if="error" class="max-w-3xl mx-auto mt-10 py-4 text-center text-lg bg-red-500 bg-opacity-10 border border-red-300 rounded-md shadow text-red-800">
            Error processing your request. Got:<br>
            <strong>{{ error }}</strong><br>
            Please try again later.
        </div>
    </div>

    <footer v-if="searchModel.response && searchModel.maxPage > 0" class="my-16 mx-auto max-w-3xl text-center">
        <pagination v-model:page="searchModel.page" :max-page="searchModel.maxPage" :page-size="searchModel.pageSize"
                    @update:page="search()" />
    </footer>
</div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { buildQueryString } from '@/common'

import SearchHeader from '@/components/SearchHeader'
import SearchResult from '@/components/SearchResult'
import Pagination from '@/components/Pagination'
import { SearchModel } from '@/search-model'

const route = useRoute()
const router = useRouter()

const searchHeaderRef = ref(null)
const resultsElement = ref(null)

const requestToken = window.DATA.token

const searchModel = reactive(new SearchModel())
const requestProgress = ref(0)
const error = ref(null)

/**
 * Request search result JSON from the server.
 */
async function requestResults() {
    // Refresh stale search token
    if (Date.now() / 1000 - requestToken.timestamp >= requestToken.max_age) {
        location.reload()
        return
    }

    if (!route.query.q) {
        return;
    }

    const baseUrl = process.env.VUE_APP_BACKEND_ADDRESS + route.path.substr(1)
    const backend = baseUrl +'search'
    const requestOptions = {
        method: 'POST',
        url: backend + '?' + buildQueryString(route.query),
        headers: {
            'Content-Type': 'application/json',
            'X-Token': requestToken.token
        },
        data: {},
        timeout: 25000,
        onDownloadProgress(e) {
            requestProgress.value = Math.max(Math.round((e.loaded * 100) / e.total), requestProgress.value)
        }
    }

    try {
        if (resultsElement.value) {
            resultsElement.value.classList.add('opacity-50', 'pointer-events-none')
        }
        requestProgress.value = 25
        error.value = ''

        const response = await axios(requestOptions)
        requestToken.token = response.headers['x-token']
        requestToken.timestamp = Date.now() / 1000

        return response.data
    } catch (ex) {
        if (ex.code === 'ECONNABORTED') {
            error.value = 'Search took too long (Timeout).'
        } else if (ex.response.status === 403 && location.hash !== '#reload') {
            // Probably a CSRF token error, try to refresh page
            location.hash = 'reload'
            location.reload()
        } else if (ex.response.status !== 200) {
            error.value = `${ex.response.status} ${ex.response.statusText}`
        }
        return new Promise(() => {})
    } finally {
        requestProgress.value = 100
        if (resultsElement.value) {
            resultsElement.value.classList.remove('opacity-50', 'pointer-events-none')
        }
    }
}

/**
 * Initiate a search request.
 */
async function search() {
    await router.push({name: 'IndexSearch', query: searchModel.toQueryString()})
    if (searchModel.query) {
        const results = await requestResults()
        if (Object.keys(results).length === 0) {
            return
        }
        searchModel.updateFromResponse(results)
    }
}

function numFormat(num, opts) {
    return num.toLocaleString('en-US', opts)
}

onMounted(() => {
    search()
})
</script>
