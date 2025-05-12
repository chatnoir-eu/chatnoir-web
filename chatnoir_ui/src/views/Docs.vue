<!--
    Copyright 2025 Janek Bevendorff

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
<div class="search-page">
    <search-header />
    <div ref="docComponent" class="search-page-body"></div>
</div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import SearchHeader from '@/components/SearchHeader.vue'
import xhr from '@/xhr.mjs'

const route = useRoute()
const docComponent = ref(null)

onMounted(async () => {
    let docTemplate = document.querySelector('#doc')
    if (!docTemplate) {
        docTemplate = (await xhr.get(
            import.meta.env.VITE_BACKEND_ADDRESS + route.fullPath.substring(1),
            {responseType: 'document'}
        )).data.querySelector('#doc')
    }
    docComponent.value.appendChild(docTemplate.content)
})
</script>
