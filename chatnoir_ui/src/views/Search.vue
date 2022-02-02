<!--
    Search page view.

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
    <search-header ref="searchHeaderRef" v-model="searchHeaderModel" focus :progress="requestProgress" @submit="search()" />

    <div v-if="searchResults.length" ref="resultsElement" key="search-results" class="max-w-3xl mx-auto">
        <div class="flex -mb-3 text-sm">
            <div class="flex-grow">
                Search results {{ numFormat(searchResultsMeta.results_from + 1) }}–{{ numFormat(searchResultsMeta.results_to) }}
                for <em class="font-bold">“{{ searchResultsMeta.query_string }}”</em>
            </div>
            <div>
                Total results: {{ numFormat(searchResultsMeta.total_results) }}<span v-if="searchResultsMeta.terminated_early">+</span>
                <span v-if="searchResultsMeta.query_time < 1500">
                    (retrieved in {{ numFormat(searchResultsMeta.query_time) }}&thinsp;ms)
                </span>
                <span v-else>
                    (retrieved in {{ numFormat(searchResultsMeta.query_time / 1000, { minimumFractionDigits: 1 }) }}&thinsp;s)
                </span>
            </div>
        </div>

        <div v-for="result in searchResults" :key="result.uuid">
            <component :is="SearchResult" :data="result" :meta="searchResultsMeta" />
        </div>
    </div>
    <div v-if="!error && searchResultsMeta && searchResults.length === 0" class="max-w-3xl mt-12 mx-auto text-center text-lg">
        No results found… ;-(
    </div>
    <div v-if="error" class="max-w-3xl mx-auto mt-10 py-4 text-center text-lg bg-red-500 bg-opacity-10 border border-red-300 rounded-md shadow text-red-800">
        Error processing your request. Got:<br>
        <strong>{{ error }}</strong><br>
        Please try again later.
    </div>

    <footer v-if="paginationModel.maxPage > 0" class="my-16 mx-auto max-w-3xl text-center">
        <pagination v-model="paginationModel" @pageChanged="search()" />
    </footer>
</div>
</template>

<script setup>
import { ref, toRefs, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { buildQueryString, searchModelToQueryString } from '@/common'

import SearchHeader from '@/components/SearchHeader'
import SearchResult from '@/components/SearchResult'
import Pagination from '@/components/Pagination'

const route = useRoute()
const router = useRouter()

const searchHeaderRef = ref(null)
const resultsElement = ref(null)

const requestToken = window.DATA.token

const searchHeaderModel = ref({})
const searchResults = ref([])
const searchResultsMeta = ref(null)
const paginationModel = ref({
    page: 0,
    maxPage: 0,
    paginationSize: 0
})
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
            resultsElement.value.classList.add('opacity-50')
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
            resultsElement.value.classList.remove('opacity-50')
        }
    }
}

/**
 * Process and display search results.
 *
 * @param resultObj result JSON
 */
function processResults(resultObj) {
    if (Object.keys(resultObj).length === 0) {
        return
    }

    searchResults.value = resultObj.hits
    searchResultsMeta.value = resultObj.meta
    searchHeaderModel.value.indices = resultObj.meta.indices_all
    paginationModel.value.page = resultObj.meta.current_page
    paginationModel.value.maxPage = resultObj.meta.max_page
    paginationModel.value.paginationSize = resultObj.meta.pagination_size
}

/**
 * Initiate a search request.
 */
async function search() {
    const queryString = searchModelToQueryString(searchHeaderModel.value)
    if (paginationModel.value.page > 1) {
        queryString['p'] = paginationModel.value.page
    }
    await router.push({name: 'IndexSearch', query: queryString})
    if (searchHeaderModel.value.query) {
        const results = await requestResults()
        processResults(results)
    }
}

function numFormat(num, opts) {
    return num.toLocaleString('en-US', opts)
}
</script>
