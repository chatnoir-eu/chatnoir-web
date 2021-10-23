<!--
    Hybrid index/search page view.
    Renders either the index or search view depending on whether a search query is given.
-->

<template>
<index-view v-if="!$route.query.q"/>
<search-view v-else/>
</template>

<script>
import IndexView from './Index'
import SearchView from './Search'

export default {
    name: 'IndexSearch',
    components: {
        IndexView,
        SearchView
    }
}
</script>
