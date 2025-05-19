<!--
    Search page view.

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
<header class="border-b mb-5 pt-5 -mx-5">
    <div class="mx-5">
        <div class="text-center sm:hidden">
            <router-link to="/">
                <inline-svg class="inline-block h-10 mt-1" :src="iconChatNoir" alt="" />
            </router-link>
        </div>
        <div class="flex flex-row items-center max-w-3xl mx-auto h-24">
            <cat-logo ref="catLogoElement" class="w-32 mr-6 hidden sm:block" router-target="/" />
            <search-field ref="searchFieldRef" v-model="searchFieldModel" :focus="focus"
                          @submit="submitSearch()" @change="$refs.catLogoElement.purr()" @ready="emit('ready')" />
        </div>
    </div>

    <progress-bar :progress="requestProgress" class="mt-3" @complete="requestProgress = 0" />
</header>
</template>

<script setup>
import { onMounted, ref, toRef, watch } from 'vue'
import CatLogo from '@/components/CatLogo.vue';
import SearchField from '@/components/SearchField.vue';
import ProgressBar from '@/components/ProgressBar.vue'
import { SearchModel } from '@/search-model.mjs'
import { useRoute, useRouter } from 'vue-router'

import iconChatNoir from '@/assets/icons/chatnoir.svg'

const route = useRoute()
const router = useRouter()

const emit = defineEmits(['ready', 'update:modelValue', 'submit'])
const props = defineProps({
    action: {type: String, default:''},
    method: {type: String, default: "GET"},
    modelValue: {
        type: SearchModel,
        default: () => new SearchModel()
    },
    progress: {type: Number, default: 0},
    focus: {type: Boolean, default: false},
    noReroute: {type: Boolean, default: false},
})

const searchFieldRef = ref(null)
const searchFieldModel = ref(null)
const requestProgress = ref(0)

async function submitSearch() {
    if (!props.noReroute) {
        await router.push({name: 'IndexSearch', query: searchFieldModel.value.toQueryStringObj()})
    }
    emit('submit', searchFieldModel.value)
}

onMounted(async () => {
    searchFieldModel.value = props.modelValue
    if (!searchFieldModel.value.query) {
        await searchFieldModel.value.updateFromQueryString(route.query)
    }
})

watch(() => props.modelValue, (newValue) => {
    searchFieldModel.value = newValue
}, {deep: true})

watch(searchFieldModel, (newValue) => {
    emit('update:modelValue', newValue)
})

watch(toRef(props, 'progress'), (newValue) => {
    requestProgress.value = newValue
})

defineExpose({
    focus: (options = {}) => searchFieldRef.value.focus(options),
    blur: () => searchFieldRef.value.blur()
})

onMounted(() => {
    // Hide browser address bar
    setTimeout(() => window.scrollTo(0, 1), 0)
})
</script>
