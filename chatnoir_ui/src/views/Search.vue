<!--
    Search page view.
-->
<template>
<div class="mx-auto max-w-full">
    <header :class="$style['search-header']">
        <div :class="$style.logo">
            <router-link to="/">
                <cat-logo ref="catLogoElement" />
            </router-link>
        </div>

        <keep-alive>
            <search-field ref="searchFieldRef" key="search-box" v-model="formData" @change="$refs.catLogoElement.purr()" />
        </keep-alive>
    </header>

    <keep-alive>
        <div ref="resultElement" key="search-results"></div>
    </keep-alive>
</div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import CatLogo from '@/components/CatLogo';
import SearchField from '@/components/SearchField';

const route = useRoute()
const router = useRouter()
const formData = ref({q: '', index: []})
const searchFieldRef = ref(null)
const resultElement = ref(null)

function buildformData(params) {
    return Object.keys(params).map(k => encodeURIComponent(k) + '=' + encodeURIComponent(params[k])).join('&')
}

async function request() {
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

    const response = await fetch(backend + '?' + buildformData(route.query), requestOptions)
    window.TOKEN = response.headers.get('X-Token')
    return response.json()
}

function processResults(resultObj) {
    resultElement.value.innerText = JSON.stringify(resultObj)
}

watch(formData, async () => {
    if (formData.value.q !== route.query.q) {
        await router.push({name: 'IndexSearch', query: formData.value})
    }

    if (formData.value.q) {
        const results = await request(formData.value.q)
        processResults(results)
    }
})

onMounted(() => {
    searchFieldRef.value.focus()
    if (route.query.q) {
        formData.value = route.query
    }
})

</script>

<style module>
.search-header {
    @apply flex flex-row items-center;
}

.logo {
    @apply w-32 mr-3;
}

</style>
