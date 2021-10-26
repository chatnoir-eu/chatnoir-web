<!--
    Index page view.
-->
<template>
<div class="mx-auto max-w-full h-full flex flex-row items-center">
    <div class="block mx-auto max-w-full mt-10 mb-36 sm:mb-64 text-center">
        <cat-logo ref="catLogoElement" class="block h-40" />

        <keep-alive>
            <search-field ref="searchFieldRef" key="search-box" v-model="formData" @change="$refs.catLogoElement.purr()" />
        </keep-alive>
    </div>
</div>
</template>

<script setup>
import { onMounted, ref, watch } from "vue";
import { useRouter } from 'vue-router'

import CatLogo from '@/components/CatLogo';
import SearchField from '@/components/SearchField';

const searchFieldRef = ref(null)
const formData = ref({q: '', index: []})

onMounted(() => {
    searchFieldRef.value.focus()
})

const router = useRouter()
watch(formData, (newValue) => {
    router.push({name: 'IndexSearch', query: newValue})
})
</script>
