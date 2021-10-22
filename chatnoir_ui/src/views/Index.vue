<!--
    Index page view.
-->
<template>

<div class="mx-auto max-w-full h-full flex flex-row items-center">
    <div class="block mx-auto max-w-full mt-10 mb-36 sm:mb-64 text-center">
        <cat-logo class="block" ref="cat-logo"/>
        <form ref="search-form" @submit="searchSubmit($event)">
            <search-field @changed="$refs['cat-logo'].purr()" />
        </form>
    </div>
</div>

</template>

<script>
import CatLogo from '@/components/CatLogo';
import SearchField from '@/components/SearchField';

export default {
    name: 'Index',
    components: {
        CatLogo,
        SearchField,
    },
    mounted() {
        document.title = 'ChatNoir'
    },
    methods: {
        searchSubmit(e) {
            e.preventDefault()
            this.$router.push({name: 'IndexSearch', query: {q: e.target.elements.q.value}})
        }
    }
}
</script>

<style>

</style>
