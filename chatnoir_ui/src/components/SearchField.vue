<template>
<div :class="$style['search-field']">
    <div>
        <input ref="searchInput" type="search" name="q" placeholder="Search…" class="text-field" role="searchbox" autofocus autocomplete="off"
               v-bind="$attrs" @input="value = $event.target.value" @keyup="emit('keyup')">
        <button type="submit">
            <inline-svg :src="require('@/assets/icons/search.svg').default" arial-label="Search" focusable="false" />
        </button>
    </div>
</div>
</template>

<script>
export default {
    inheritAttrs: false
}
</script>

<script setup>
import { onMounted, ref, watch } from 'vue';
import InlineSvg from 'vue-inline-svg';

const emit = defineEmits(['change', 'keyup'])
const searchInput = ref(null)
const value = ref('')

function focus() {
    searchInput.value.focus()
}

function setValue(newValue) {
    value.value = newValue
}

onMounted(() => {
    value.value = searchInput.value.value

    watch(value, (newValue, oldValue) => {
        if (newValue !== oldValue) {
            searchInput.value.value = newValue
            emit('change', {newValue, oldValue})
        }
    })
})

defineExpose({
    focus,
    value,
    setValue
})
</script>

<style module>
.search-field {
    width: 40rem;
    @apply max-w-full;
    @apply inline-block;

    & > div {
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
