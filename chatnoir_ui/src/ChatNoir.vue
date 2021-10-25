<template>
<section id="app" class="flex flex-col h-screen">
    <main class="flex-grow w-full px-8 py-3">
        <router-view :key="$route.path" />
    </main>

    <webis-footer
        copyright-start-year="2012"
        contact-fragment="#bevendorff"
        :additional-links="[{href: 'https://webis.de/publications.html?q=bevendorff_2018', anchor: 'Cite'}]"
    />
</section>
</template>

<script setup>
import WebisFooter from '@/components/WebisFooter'
</script>
