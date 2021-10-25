<template>
<div :class="$style['search-field']">
    <form :class="$style.search" :action="action" :method="method"
          @submit.prevent="$emit('update:modelValue', currentValue)">
        <input ref="searchInput" type="search" name="q" placeholder="Search…"
               class="text-field" role="searchbox" autocomplete="off" spellcheck="false"
               v-bind="$attrs" :value="modelValue"
               @input="currentValue = $event.target.value" @keyup="emit('keyup', $event)">
        <button type="submit">
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

const emit = defineEmits(['update:modelValue', 'change', 'keyup'])
const searchInput = ref(null)
const currentValue = ref('')
const props = defineProps({
    action: {type: String, default:''},
    method: {type: String, default: "GET"},
    modelValue: {type: String, default: ''}
})

function focus() {
    searchInput.value.focus()
}

watch(toRef(props, 'modelValue'), (newValue) => {
    currentValue.value = newValue
})

watch(currentValue, (newValue, oldValue) => {
    if (newValue !== oldValue) {
        searchInput.value.value = newValue
        emit('change', newValue)
    }
})

defineExpose({
    focus,
    currentValue
})
</script>

<style module>
.search-field {
    width: 40rem;
    @apply max-w-full;
    @apply inline-block;

    & > form {
        @apply box-border;
        @apply py-3 px-5;
        @apply relative;
    }

    input[type="search"] {
        @apply w-full;
        @apply px-6 py-3;
        @apply m-0;
    }

    button {
        @apply absolute;
        @apply outline-none;
        @apply text-gray-400;
        @apply mr-10;
        height: 1rem;
        top: calc(50% - .5rem);
        right: 0;

        svg {
            @apply fill-current;
            @apply h-full;
        }
    }

    &:hover button, button:hover,
    &:focus-within button, button:focus{
        @apply text-red;
    }

    &:focus-within input[type="search"] {
        @apply shadow-md;
    }
}

</style>
