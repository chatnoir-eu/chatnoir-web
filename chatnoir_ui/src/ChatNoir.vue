<template>

<section id="app" class="flex flex-col h-screen justify-between">
  <search-field/>

  <webis-footer/>
</section>

</template>

<script>
import SearchField from "@/components/SearchField";
import WebisFooter from "@/components/WebisFooter";

export default {
    name: 'ChatNoirApp',
    components: {
        SearchField,
        WebisFooter
    }
}
</script>

<style>

</style>
