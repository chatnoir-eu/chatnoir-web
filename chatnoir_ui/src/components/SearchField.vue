<template>
<div class="text-left" :class="$style['search-field']">
    <form :class="$style.search" :action="action" :method="method" @submit.prevent="emitSubmit()">
        <input ref="searchInput" type="search" name="q" placeholder="Search…"
               class="text-field" role="searchbox" autocomplete="off" spellcheck="false"
               v-bind="$attrs" :value="modelValue.q"
               @input="currentValue = $event.target.value" @keyup="emit('keyup', $event)">

        <button ref="optionsButtion" type="button" :class="$style['btn-settings']" @click="showOptions = !showOptions">
            <inline-svg :src="require('@/assets/icons/settings.svg').default" arial-label="Options" />
        </button>
        <transition name="fade">
            <options-drop-down
                v-model="optionsModel"
                :visible="showOptions"
                :ref-element="$refs.optionsButtion"
                @close="showOptions = false"
            />
        </transition>

        <button type="submit" :class="$style['btn-submit']">
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
import { ref, toRef, watch } from 'vue';
import InlineSvg from 'vue-inline-svg';

import OptionsDropDown from './OptionsDropDown'

const emit = defineEmits(['update:modelValue', 'change', 'keyup'])
const props = defineProps({
    action: {type: String, default:''},
    method: {type: String, default: "GET"},
    modelValue: {
        type: Object,
        default: () => { return {q: '', index: []} },
        validator(value) {
            return typeof value.q === 'string' && ['object', 'string'].includes(typeof value.index)
        }
    }
})

const searchInput = ref(null)
const currentValue = ref('')
const showOptions = ref(false)
const optionsModel = ref(window.DATA.indices)

function focus() {
    searchInput.value.focus()
}

function emitSubmit() {
    const queryObj = {
        q: currentValue.value,
        index: optionsModel.value.filter((e) => e.selected).map((e) => e.id)
    }
    emit('update:modelValue', queryObj)
}

watch(toRef(props, 'modelValue'), (newValue) => {
    currentValue.value = newValue.q
})

watch(currentValue, (newValue, oldValue) => {
    if (newValue !== oldValue) {
        searchInput.value.value = newValue
        emit('change', newValue)
    }
})

defineExpose({
    focus,
    currentValue,
    optionsModel
})
</script>

<style module>
.search-field {
    width: 40rem;
    @apply max-w-full;
    @apply inline-block;
    @apply relative;

    & > form {
        @apply box-border;
        @apply py-3 px-5;
        @apply relative;
    }

    input[type="search"] {
        @apply w-full;
        @apply px-6 py-3;
        @apply pr-20;
        @apply m-0;
    }

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

    .btn-submit {
        @apply mr-10;
    }

    .btn-settings {
        @apply mr-20;
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
