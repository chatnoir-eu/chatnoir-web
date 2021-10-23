<!--
    Search page view.
-->

<template>

<div class='mx-auto max-w-full'>
Search Results.
</div>

</template>

<script>
function buildQueryString(params) {
    return Object.keys(params).map(k => encodeURIComponent(k) + '=' + encodeURIComponent(params[k])).join('&')
}

async function request(vue) {
    const baseUrl = window.location.origin + vue.$route.path
    const backend = baseUrl + (baseUrl.endsWith('/') ? '' : '/') + 'search'

    const requestOptions = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Token': window.TOKEN
        },
        body: JSON.stringify({})
    };

    const response = await fetch(backend + '?' + buildQueryString(vue.$route.query), requestOptions)
    window.TOKEN = response.headers.get('X-Token')
    return response.json()
}

export default {
    mounted() {
        request(this).then(r => {
            console.log(r)

            request(this).then(r => {
                console.log(r)
            })
        })
    }
}
</script>

<style>

</style>
