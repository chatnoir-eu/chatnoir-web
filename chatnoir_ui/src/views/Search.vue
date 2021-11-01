<!--
    Search page view.
-->
<template>
<div class="mx-auto max-w-full">
    <header class="border-b mb-10 pt-1 pb-2">
        <div class="flex flex-row items-center max-w-3xl mx-auto">
            <div class="w-32 mr-3">
                <router-link to="/">
                    <cat-logo ref="catLogoElement" />
                </router-link>
            </div>

            <keep-alive>
                <search-field ref="searchFieldRef" key="search-box2"
                              v-model="searchModel" @submit="search()" @change="$refs.catLogoElement.purr()" />
            </keep-alive>
        </div>
    </header>

    <div v-if="searchResults.length" ref="resultsElement" key="search-results" class="max-w-3xl mx-auto">
        <div v-for="result in searchResults" :key="result.uuid">
            <component :is="SearchResult" :data="result" />
        </div>
    </div>
</div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { buildQueryString } from '@/common';

import CatLogo from '@/components/CatLogo';
import SearchField from '@/components/SearchField';
import SearchResult from '@/components/SearchResult'

const route = useRoute()
const router = useRouter()
const searchModel = ref({})
const searchFieldRef = ref(null)
const resultsElement = ref(null)
const searchResults = ref([])

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
    };

    const response = await fetch(backend + '?' + buildQueryString(route.query), requestOptions)
    window.TOKEN = response.headers.get('X-Token')
    return response.json()
}

/**
 * Process and display search results.
 *
 * @param resultObj result JSON
 */
function processResults(resultObj) {
    console.log(resultObj.hits)
    searchResults.value = resultObj.hits
}

/**
 * Initiate a search request.
 *
 * @param initialLoad whether this is the initial page load (will not manipulate routes)
 */
async function search(initialLoad = false) {
    if (!initialLoad) {
        const routeQuery = searchFieldRef.value.modelToQueryString()
        if (JSON.stringify(routeQuery) !== JSON.stringify(route.query)) {
            await router.push({name: 'IndexSearch', query: routeQuery})
        }
    }
    if (searchModel.value.query) {
        const results = await requestResults()
        processResults(results)
    }
}

onMounted(() => {
    searchFieldRef.value.focus()
    search(true)
})
</script>
