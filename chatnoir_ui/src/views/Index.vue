<!--
    Copyright 2021 Janek Bevendorff

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
<div class="max-w-full h-full flex flex-row items-center">
    <div class="block mx-auto max-w-full mb-[12svh] sm:mb-[27svh] text-center px-7">
        <cat-logo ref="catLogoElement" class="block text-center h-40" />
        <search-field ref="searchFieldRef" v-model="searchModel" focus
                      @submit="search()" @change="$refs.catLogoElement.purr()" />

        <div v-if="getModuleName() === 'chatnoir'" class="text-xs my-1 text-right">
            <a href="https://old.chatnoir.eu/" title="It's still there (for now&hellip;)">Looking for the old ChatNoir?</a>
        </div>
    </div>
</div>
</template>

<script setup>
import { ref } from "vue"
import { useRouter } from 'vue-router'

import CatLogo from "@/components/CatLogo.vue";
import SearchField from '@/components/SearchField.vue'
import { SearchModel } from '@/search-model.mjs'

const router = useRouter()
const searchFieldRef = ref(null)
const searchModel = ref(new SearchModel())

function search() {
    if (searchModel.value.query) {
        router.push({name: 'IndexSearch', query: searchModel.value.toQueryStringObj()})
    }
}

function getModuleName() {
    return window._APP_SETTINGS.app_module
}
</script>
