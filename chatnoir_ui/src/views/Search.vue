<!--
    Search page view.
-->
<template>
<div class="mx-auto max-w-full">
    Search Results.
</div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useRoute } from 'vue-router';

function buildQueryString(params) {
    return Object.keys(params).map(k => encodeURIComponent(k) + '=' + encodeURIComponent(params[k])).join('&')
}

const route = useRoute()

async function request() {
    const baseUrl = window.location.origin + route.path
    const backend = baseUrl + (baseUrl.endsWith('/') ? '' : '/') + 'search'

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

onMounted(() => {
    request(this).then(r => {
        console.log(r)

        request(this).then(r => {
            console.log(r)
        })
    })
})

</script>
