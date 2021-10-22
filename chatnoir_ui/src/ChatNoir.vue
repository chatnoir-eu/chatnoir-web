<template>

<section id="app" class="flex flex-col h-screen">
    <main class="flex-grow flex flex-row items-center w-full">
        <div class="block mx-auto max-w-full mt-10 mb-32 sm:mb-64 text-center">
            <cat-logo class="block" ref="cat-logo"/>
            <search-field @changed="$refs['cat-logo'].purr()" />
        </div>
    </main>

    <webis-footer
        copyright-start-year="2012"
        contact-fragment="#bevendorff"
        :additional-links="[{href: 'https://webis.de/publications.html?q=bevendorff_2018', anchor: 'Cite'}]"
    />
</section>

</template>

<script>
import CatLogo from "@/components/CatLogo";
import SearchField from "@/components/SearchField";
import WebisFooter from "@/components/WebisFooter";

export default {
    name: 'ChatNoirApp',
    components: {
        CatLogo,
        SearchField,
        WebisFooter
    },
    mounted() {
        document.title = 'ChatNoir'
    }
}
</script>

<style>

</style>
