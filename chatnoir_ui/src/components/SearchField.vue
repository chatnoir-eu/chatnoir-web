<template>
<div class="text-left max-w-full inline-block relative" :class="$style['search-field']">
    <form class="box-border py-3 px-5 relative"
          :action="action" :method="method" @submit.prevent="emitModelUpdate(true)">
        <input ref="searchInput" v-model="queryString"
               class="text-field w-full px-6 py-3 pr-20 m-0"
               type="search" name="q" placeholder="Search…"
               role="searchbox" autocomplete="off" spellcheck="false"
               v-bind="$attrs"
               @keyup="emit('keyup', $event)">

        <button ref="optionsButton" type="button" class="mr-20" :class="$style['btn-options']" @click="showOptions = !showOptions">
            <inline-svg :src="require('@/assets/icons/settings.svg').default" arial-label="Options" />
        </button>
        <options-drop-down
            v-model="optionsModel"
            :visible="showOptions"
            :ref-element="$refs.optionsButton"
            @close="showOptions = false"
        />

        <button type="submit" class="mr-10" :class="$style['btn-submit']">
            <inline-svg :src="require('@/assets/icons/search.svg').default" arial-label="Search" />
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
import { onMounted, ref, toRef, watch } from 'vue';
import InlineSvg from 'vue-inline-svg';

import OptionsDropDown from './OptionsDropDown'
import { useRoute } from 'vue-router';

const emit = defineEmits(['update:modelValue', 'submit', 'change', 'option-change', 'keyup'])
const props = defineProps({
    action: {type: String, default:''},
    method: {type: String, default: "GET"},
    modelValue: {
        type: Object,
        default: () => { return {query: '', indices: []} },
        validator(value) {
            return typeof value.query === 'string' && value.indices.every((e) => e.id && e.name)
        }
    }
})

const route = useRoute()
const searchInput = ref(null)
const queryString = ref('')
const showOptions = ref(false)
const optionsModel = ref([])

function focus() {
    searchInput.value.focus()
}

function emitModelUpdate(submit = false) {
    const ctx = {
        query: queryString.value,
        indices: optionsModel.value
    }
    emit('update:modelValue', ctx)
    if (submit) {
        emit('submit', ctx)
    }
}

/**
 * Update model data from the current route's query string.
 *
 * @returns {{query: string, indices: object}}
 */
function updateModelFromQueryString() {
    let indices = route.query.index || []
    if (typeof route.query.index === 'string') {
        indices = [route.query.index]
    }

    emit('update:modelValue', {
        query: route.query.q || '',
        indices: window.DATA.indices.map((i) => Object.assign(
            {}, i, {selected: !indices.length ? i.selected : indices.includes(i.id)}))
    })
}

/**
 * Generate a query string object representation of the current model.
 *
 * @returns {{} | {q: string, index: *[]}}
 */
function modelToQueryString() {
    if (!props.modelValue) {
        return {}
    }
    let indices = props.modelValue.indices.filter((e) => e.selected).map((e) => e.id)
    return {
        q: props.modelValue.query,
        index: indices.length === 1 ? indices[0] : indices
    }
}

watch(toRef(props, 'modelValue'), (newValue) => {
    queryString.value = newValue.query
    optionsModel.value = newValue.indices || []
})

watch(queryString, (newValue, oldValue) => {
    if (newValue !== oldValue) {
        emit('change', newValue)
        emitModelUpdate()
    }
})

watch(optionsModel, (newValue, oldValue) => {
    if (newValue !== oldValue) {
        emit('option-change', newValue)
        emitModelUpdate()
    }
})

defineExpose({
    focus,
    modelToQueryString
})

onMounted(() => {
    if (!props.modelValue) {
        updateModelFromQueryString()
    }
})
</script>

<style module>
.search-field {
    width: 40rem;

    button {
        @apply absolute;
        @apply outline-none;
        @apply text-gray-400;
        height: 1rem;
        top: calc(50% - .5rem);
        right: 0;

        svg {
            @apply fill-current;
            @apply h-full;
        }
    }

    &:hover, &:focus-within .btn-submit,
    button:hover, button:focus {
        @apply text-red;
    }

    &:focus-within input[type="search"] {
        @apply shadow-md;
    }
}
</style>
