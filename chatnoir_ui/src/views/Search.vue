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
<div class="mx-auto max-w-full px-5">
    <header class="border-b mb-5 pt-5 -mx-5">
        <div class="flex flex-row items-center max-w-3xl mx-auto h-24 px-5">
            <div class="w-32 mr-3 hidden sm:block">
                <router-link to="/">
                    <cat-logo ref="catLogoElement" />
                </router-link>
            </div>

            <keep-alive>
                <search-field ref="searchFieldRef" key="search-box2"
                              v-model="searchFieldModel" @submit="updateRoute()" @change="$refs.catLogoElement.purr()" />
            </keep-alive>
        </div>

        <progress-bar :progress="requestProgress" class="mt-3" @complete="requestProgress = 0" />
    </header>

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
            <component :is="SearchResult" :data="result" />
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
        <pagination v-model="paginationModel" />
    </footer>
</div>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios'
import { buildQueryString } from '@/common';

import CatLogo from '@/components/CatLogo';
import SearchField from '@/components/SearchField';
import SearchResult from '@/components/SearchResult'
import ProgressBar from '@/components/ProgressBar'
import Pagination from '@/components/Pagination'

const route = useRoute()
const router = useRouter()

const searchFieldRef = ref(null)
const resultsElement = ref(null)

const requestToken = window.DATA.token

const searchFieldModel = ref({})
const searchResults = ref([])
const searchResultsMeta = ref(null)
const paginationModel = reactive({
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
        onDownloadProgress(e) {
            requestProgress.value = Math.max(Math.round((e.loaded * 100) / e.total), requestProgress.value)
        }
    }

    try {
        requestProgress.value = 25
        error.value = ''
        const response = await axios(requestOptions)
        requestToken.token = response.headers['x-token']
        requestToken.timestamp = Date.now() / 1000
        return response.data
    } catch (ex) {
        if (ex.response.status === 403 && location.hash !== '#reload') {
            // Probably a CSRF token error, try to refresh page
            location.hash = 'reload'
            location.reload()
        } else if (ex.response.status !== 200) {
            error.value = `${ex.response.status} ${ex.response.statusText}`
        }
        return new Promise(() => {})
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
    searchFieldModel.value.indices = resultObj.meta.indices_all
    paginationModel.page = resultObj.meta.current_page
    paginationModel.maxPage = resultObj.meta.max_page
    paginationModel.paginationSize = resultObj.meta.pagination_size
}

/**
 * Update route which current model data, which will trigger a search request.
 */
async function updateRoute() {
    const routeQuery = searchFieldRef.value.modelToQueryString()
    if (JSON.stringify(routeQuery) !== JSON.stringify(route.query)) {
        await router.push({name: 'IndexSearch', query: routeQuery})
    }
}

/**
 * Initiate a search request.
 */
async function search() {
    if (searchFieldModel.value.query) {
        const results = await requestResults()
        processResults(results)
    }
}

function numFormat(num, opts) {
    return num.toLocaleString('en-US', opts)
}

onMounted(() => {
    searchFieldRef.value.focus()
    search()
})

watch(() => route.query, () => {
    search()
})
</script>
