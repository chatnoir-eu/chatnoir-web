<!--
    Index page view.
-->
<template>
<div class="mx-auto max-w-full h-full flex flex-row items-center">
    <div class="block mx-auto max-w-full mt-10 mb-36 sm:mb-64 text-center">
        <cat-logo ref="catLogoElement" class="block" />
        <form ref="search-form" @submit.prevent="searchSubmit($event)">
            <search-field @change="$refs.catLogoElement.purr()" />
        </form>
    </div>
</div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from 'vue-router'

import CatLogo from '@/components/CatLogo';
import SearchField from '@/components/SearchField';

onMounted(() => document.title = 'ChatNoir')

const router = useRouter()
function searchSubmit(e) {
    router.push({name: 'IndexSearch', query: {q: e.target.elements.q.value}})
}
</script>
