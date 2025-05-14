<template>
<section id="app" class="flex flex-col h-screen">
    <main class="flex-grow w-full">
        <router-view :key="$route.path" />
    </main>
    <webis-footer copyright-start-year="2012" contact-fragment="#bevendorff" :additional-links="getFooterLinks()" />
</section>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import WebisFooter from '@/components/WebisFooter.vue'

const router = useRouter()

function getFooterLinks() {
    const links = [
        {href: 'https://webis.de/publications.html?q=bevendorff_2018', anchor: 'Cite'},
    ]
    if (window._APP_SETTINGS.app_module === 'chatnoir') {
        links.push(
            {href: router.resolve({name: 'ApikeyRequest'}), anchor: 'Request API Key'},
            {href: router.resolve({name: 'Docs'}), anchor: 'API Documentation'}
        )
    } else {
        links.push({href: 'https://www.chatnoir.eu/', anchor: 'ChatNoir'})
    }
    return links
}

onMounted(() => {
    // Hide browser address bar
    setTimeout(() => window.scrollTo(0, 1), 0)
})
</script>
