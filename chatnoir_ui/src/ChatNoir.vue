<template>
<section id="app" class="flex flex-col h-screen">
    <main class="flex-grow w-full">
        <router-view :key="$route.path" />
    </main>

    <webis-footer
        copyright-start-year="2012"
        contact-fragment="#bevendorff"
        :additional-links="[
            {href: 'https://webis.de/publications.html?q=bevendorff_2018', anchor: 'Cite'},
            {href: $router.resolve({name: 'ApikeyRequest'}), anchor: 'Request API Key'},
            {href: $router.resolve({name: 'Docs'}).fullPath, anchor: 'API Documentation'},
        ]"
    />
</section>
</template>

<script setup>
import { onMounted } from 'vue'
import WebisFooter from '@/components/WebisFooter.vue'

onMounted(() => {
    // Hide browser address bar
    setTimeout(() => window.scrollTo(0, 1), 0)
})
</script>
