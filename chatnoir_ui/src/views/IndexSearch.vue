<!--
    Hybrid index/search page view.
    Renders either the index or search view depending on whether a search query is given.
-->
<template>
<component :is="$route.query.q ? Search : Index" />
</template>

<script setup>
import Index from './Index'
import Search from './Search'
</script>
