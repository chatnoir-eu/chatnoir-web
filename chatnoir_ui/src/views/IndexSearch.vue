<!--
    Hybrid index/search page view.
    Renders either the index or search view depending on whether a search query is given.
-->
<template>
<keep-alive>
    <component :is="$route.query.q ? Search : Index" />
</keep-alive>
</template>

<script setup>
import Index from './Index'
import Search from './Search'
</script>
