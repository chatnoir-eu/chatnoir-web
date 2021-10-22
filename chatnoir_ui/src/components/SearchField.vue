<template>
<div :class="$style['search-field']">
    <input type="search" name="q" placeholder="Search…" class="text-field" role="searchbox" autofocus autocomplete="off"
           v-bind="$attrs" @keyup="changed()" ref="search-field">
    <button type="submit">
        <svg aria-hidden="true" focusable="false" role="img" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
            <path d="M505 442.7L405.3 343c-4.5-4.5-10.6-7-17-7H372c27.6-35.3 44-79.7 44-128C416 93.1 322.9 0 208 0S0 93.1 0 208s93.1 208 208 208c48.3 0 92.7-16.4 128-44v16.3c0 6.4 2.5 12.5 7 17l99.7 99.7c9.4 9.4 24.6 9.4 33.9 0l28.3-28.3c9.4-9.4 9.4-24.6.1-34zM208 336c-70.7 0-128-57.2-128-128 0-70.7 57.2-128 128-128 70.7 0 128 57.2 128 128 0 70.7-57.2 128-128 128z"></path>
        </svg>
    </button>
</div>
</template>

<script>
export default {
    inheritAttrs: false,
    emits: ['changed'],
    methods: {
        changed() {
            this.$emit('changed', this)
        },
        value() {
            return this.$refs["search-field"].value
        },
        setValue(newValue) {
            let oldValue = this.$refs["search-field"].value
            this.$refs["search-field"].value = newValue
            if (oldValue !== newValue) {
                this.changed()
            }
        }
    }
}
</script>

<style module>
.search-field {
    width: 40rem;
    @apply max-w-full;
    @apply relative;
    @apply inline-block;
    @apply box-border;
    @apply py-3 px-5;

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
