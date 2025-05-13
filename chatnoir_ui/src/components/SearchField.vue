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
<div class="text-left max-w-full inline-block relative search-field">
    <form class="box-border py-3 relative"
          :action="action" :method="method" @submit.prevent="emitModelUpdate(true)">
        <input ref="searchInput" v-model="searchModel.query"
               class="text-field w-full input-xl pr-20 m-0 focus:border-gray-300"
               type="search" name="q" placeholder="Search…"
               role="searchbox" aria-label="Search" autocomplete="off" spellcheck="false"
               v-bind="$attrs"
               @keyup="emit('keyup', $event)">

        <button v-if="searchModel.indices.length > 0" ref="optionsButton" type="button" aria-label="Search options"
                class="btn-options mr-12 w-4" @click="showOptions = !showOptions">
            <inline-svg class="h-full mx-auto align-middle" :src="iconSettings" alt="Options" />
        </button>
        <options-drop-down
            v-if="searchModel.indices.length > 0"
            v-model="searchModel.indices"
            :visible="showOptions"
            :ref-element="optionsButton"
            @close="showOptions = false"
        />

        <button type="submit" class="btn-submit mr-6" aria-label="Submit search">
            <inline-svg class="h-full mx-auto align-middle icon-search" :src="iconSearch" alt="Search" />
        </button>
    </form>
</div>
</template>

<script>
export default {
    inheritAttrs: false
}
</script>

<script setup>
import { onMounted, ref, reactive, watch } from 'vue'

import { SearchModel } from '@/search-model.mjs'
import OptionsDropDown from '@/components/OptionsDropDown.vue'

import iconSettings from '@/assets/icons/settings.svg'
import iconSearch from '@/assets/icons/search.svg'

const optionsButton = ref(null)
const emit = defineEmits(['update:modelValue', 'submit', 'change', 'option-change', 'keyup'])
const props = defineProps({
    action: {type: String, default: ''},
    method: {type: String, default: 'GET'},
    modelValue: {
        type: SearchModel,
        default: () => new SearchModel()
    },
    focus: {type: Boolean, default: false}
})

const searchInput = ref(null)
const showOptions = ref(false)
const searchModel = reactive(new SearchModel())

function blur() {
    searchInput.value.blur()
}

function setFocus(options = {}) {
    searchInput.value.focus(options)
}

function emitModelUpdate(submit = false) {
    if (submit) {
        searchInput.value.blur()
        searchModel.page = 1
    }
    emit('update:modelValue', searchModel)
    if (submit) {
        emit('submit', searchModel)
    }
}

watch(() => props.modelValue, (newValue) => {
    Object.assign(searchModel, newValue)
}, {deep: true})

watch(searchModel, () => {
    emitModelUpdate()
})

watch(() => searchModel.query, (newValue) => {
    emit('change', newValue)
})

watch(() => searchModel.indices, (newValue) => {
    emit('option-change', newValue)
})

defineExpose({
    blur,
    focus
})

onMounted(() => {
    if (props.focus) {
        setFocus()
    }
    searchModel.initState()
})
</script>

<style scoped>
@reference "@/assets/css/index.css";

.search-field {
    width: 40rem;

    button {
        @apply absolute;
        @apply outline-hidden;
        @apply text-gray-400;
        height: 1rem;
        top: calc(50% - .5rem);
        right: 0;

        svg {
            @apply fill-current;
            @apply h-full;
        }
    }

    &:hover .btn-submit, &:focus-within .btn-submit,
    button:hover, button:focus {
        @apply text-red-500;
    }

    &:focus-within input[type="search"] {
        @apply shadow-md;
    }
}
</style>
