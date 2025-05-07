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
    <search-header ref="searchHeaderRef" v-model="searchModel" :progress="requestProgress" @submit="search()" />

    <div ref="resultsElement">
        <div v-if="!error && searchModel.response && searchModel.response.results.length" key="search-results" class="max-w-3xl mx-auto">
            <div class="sm:flex -mb-3 text-sm pb-2">
                <div class="sm:flex-grow">
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

            <div v-for="hit in searchModel.response.results" :key="hit.uuid">
                <component :is="SearchResult" :data="hit" :meta="searchModel.response.meta" />
            </div>
        </div>
        <div v-if="!error && searchModel.response && searchModel.response.results.length === 0" class="max-w-3xl mt-12 mx-auto text-center text-lg">
            No results found… ;-(
        </div>
        <div v-if="error" class="max-w-3xl mx-auto mt-10 py-4 text-center text-lg bg-red-500/10 border border-red-300 rounded-md shadow-sm text-red-800">
            Error processing your request. Got:<br>
            <strong>{{ error }}</strong><br>
            <span v-if="apiResponseCode === 500 || apiResponseCode === null">Please try again later.</span>
        </div>
    </div>

    <footer v-if="searchModel.response && searchModel.maxPage() > 0" class="my-16 mx-auto max-w-3xl text-center">
        <pagination v-model:page="searchModel.page" :max-page="searchModel.maxPage()" :page-size="searchModel.pageSize"
                    @update:page="search()" />
    </footer>
</div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { SearchModel } from '@/search-model.mjs'

import SearchHeader from '@/components/SearchHeader.vue'
import SearchResult from '@/components/SearchResult.vue'
import Pagination from '@/components/Pagination.vue'

const route = useRoute()
const router = useRouter()

const searchHeaderRef = ref(null)
const resultsElement = ref(null)

const searchModel = ref(new SearchModel())
const requestProgress = ref(0)
const error = ref(null)
const apiResponseCode = ref(null)

/**
 * Request search result JSON from the server.
 */
async function requestResults() {
    if (!route.query.q) {
        return;
    }
    const requestOptions = {
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
        apiResponseCode.value = 200
        const response = await searchModel.value.search(requestOptions)

        // Clear reload indicator on successful return
        if (location.hash === '#reload') {
            location.hash = ''
        }
        return response
    } catch (ex) {
        apiResponseCode.value = ex.response ? ex.response.status : null
        if (ex.code === 'ECONNABORTED' || (ex.response && ex.response.data.error === 'timeout')) {
            error.value = 'Search took too long (Timeout).'
        } else if (ex.response.status !== 200) {
            if (ex.response.data.message) {
                error.value = `${ex.response.data.message} (Error ${ex.response.data.code})`
            } else {
                error.value = `${ex.response.status} ${ex.response.statusText}`
            }
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
async function search(reroute = true) {
    if (reroute) {
        await router.push({name: 'IndexSearch', query: searchModel.value.toQueryStringObj(), hash: route.hash})
    }
    if (searchModel.value.query) {
        const results = await requestResults()
        if (Object.keys(results).length === 0) {
            return
        }
        searchModel.value.updateFromResponse(results)
    }
}

function numFormat(num, opts) {
    return num.toLocaleString('en-US', opts)
}

onMounted(() => {
    search(false)
})
</script>
