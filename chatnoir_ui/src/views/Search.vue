<!--
    Search page view.
-->
<template>
<div class="mx-auto max-w-full px-5">
    <header class="border-b mb-5 pt-5 pb-3 -mx-5">
        <div class="flex flex-row items-center max-w-3xl mx-auto h-24 px-5">
            <div class="w-32 mr-3 hidden sm:block">
                <router-link to="/">
                    <cat-logo ref="catLogoElement" />
                </router-link>
            </div>

            <keep-alive>
                <search-field ref="searchFieldRef" key="search-box2"
                              v-model="searchModel" @submit="updateRoute()" @change="$refs.catLogoElement.purr()" />
            </keep-alive>
        </div>
    </header>

    <div v-if="searchResults.length" ref="resultsElement" key="search-results" class="max-w-3xl mx-auto">
        <div class="flex -mb-3 text-sm">
            <div class="flex-grow">
                Search results {{ numFormat(searchResultsMetaExtra.results_from + 1) }}–{{ numFormat(searchResultsMetaExtra.results_to) }}
                for <em class="font-bold">“{{ searchResultsMetaExtra.query_string }}”</em>
            </div>
            <div>
                Total results: {{ numFormat(searchResultsMeta.total_results) }}<span v-if="searchResultsMetaExtra.terminated_early">+</span>
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
    <div v-if="!error && searchResultsMeta && searchResults.length === 0" class="max-w-3xl mx-auto text-center text-lg">
        No results found… ;-(
    </div>
    <div v-if="error" class="max-w-3xl mx-auto py-4 text-center text-lg bg-red-500 bg-opacity-10 border border-red-300 rounded-md shadow text-red-800">
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
import { buildQueryString } from '@/common';

import CatLogo from '@/components/CatLogo';
import SearchField from '@/components/SearchField';
import SearchResult from '@/components/SearchResult'
import Pagination from '@/components/Pagination'

const route = useRoute()
const router = useRouter()
const searchModel = ref({})
const searchFieldRef = ref(null)
const resultsElement = ref(null)
const searchResults = ref([])
const searchResultsMeta = ref(null)
const searchResultsMetaExtra = ref(null)
const paginationModel = reactive({
    page: 0,
    maxPage: 0,
    paginationSize: 0
})
const error = ref(null)

/**
 * Request search result JSON from the server.
 */
async function requestResults() {
    const baseUrl = process.env.VUE_APP_BACKEND_ADDRESS + route.path.substr(1)
    const backend = baseUrl +'search'

    const requestOptions = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Token': window.TOKEN
        },
        body: JSON.stringify({})
    }

    const response = await fetch(backend + '?' + buildQueryString(route.query), requestOptions)
    // probably CSRF token error, refresh page
    if (response.status === 403 && location.hash !== '#reload') {
        location.hash = 'reload'
        location.reload()
    } else if (response.status !== 200) {
        error.value = `${response.status} ${response.statusText}`
        return new Promise(() => {})
    }
    error.value = ''
    window.TOKEN = response.headers.get('X-Token')
    return response.json()
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
    searchResultsMetaExtra.value = resultObj.meta_extra
    paginationModel.page = resultObj.meta_extra.current_page
    paginationModel.maxPage = resultObj.meta_extra.max_page
    paginationModel.paginationSize = resultObj.meta_extra.pagination_size
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
    if (searchModel.value.query) {
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
