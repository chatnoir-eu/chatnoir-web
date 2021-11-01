<template>
<!-- eslint-disable vue/no-v-html -->
<article :id="'result-' + data.uuid" class="my-8">
    <header class="leading-tight">
        <a v-if="data.external_uri" :href="data.external_uri"
           class="text-gray-800 no-underline hover:underline focus:underline text-sm">
            {{ abbreviateUrl(data.external_uri, 2).replace(/^https?:\/\//i, '') }}
        </a>
        <h2 :class="$style.title" class="leading-none">
            <a :href="data.internal_uri" rel="nofollow"
               class="text-xl text-red-700 no-underline hover:underline focus:unterline"
               v-html="data.title"></a>
        </h2>
        <div class="text-sm text-gray-800">
            <span v-if="data.authors && data.authors.length > 0" :class="$style['meta-link']">
                <a :href="getAuthorUrl(data.authors[0])">{{ getLastName(data.authors[0]) }}</a>
                <span v-if="data.authors.length === 2"> and </span>
                <a v-if="data.authors.length === 2" :href="getAuthorUrl(data.authors[1])">{{ getLastName(data.authors[1]) }}</a>
                <span v-if="data.authors.length > 2"> et al.</span>
            </span>

            <span v-if="data.venue" :class="$style['meta-link']">
                <a :href="getQueryUrl(route, `venue:${data.venue}`)">{{ data.venue }}</a>
            </span>

            <span v-if="data.year" :class="$style['meta-link']">
                <a :href="getQueryUrl(route, `year:${data.year}`)">{{ data.year }}</a>
            </span>

            <button :ref="`opt-btn-${data.uuid}`" type="button" class="h-2.5 w-2.5 ml-3 text-center" @click="optsShown = data.uuid">
                <inline-svg :src="require('@/assets/icons/settings.svg').default" class="h-full mx-auto" arial-label="Options" />
            </button>

            <ToolTipPopup :ref-element="$refs[`opt-btn-${data.uuid}`]" :visible="optsShown === data.uuid"
                          class="tail-top max-w-md hidden" @close="optsShown = ''">
                <dl :class="$style['meta-details']">
                    <dt>Score:</dt>
                    <dd>{{ data.score.toFixed(2) }}</dd>

                    <dt v-if="data.doi">DOI:</dt>
                    <dd><a v-if="data.doi" :href="data.external_uri">{{ data.doi }}</a></dd>

                    <dt>Anthology ID:</dt>
                    <dd>{{ data.anthology_id }}</dd>

                    <dt>Authors:</dt>
                    <dd>
                        <span v-for="(a, i) in data.authors" :key="a">
                            <a :href="getAuthorUrl(a)">{{ a.replace(/\s+/, '\u00a0') }}</a>
                            <span v-if="i !== data.authors.length - 1">,<br></span>
                        </span>
                    </dd>

                    <dt>Venue:</dt>
                    <dd>{{ data.venue }}</dd>

                    <dt>Year:</dt>
                    <dd>{{ data.year }}</dd>
                </dl>
            </ToolTipPopup>
        </div>
    </header>

    <p :class="$style.snippet" class="text-gray-900 mt-1" v-html="data.snippet"></p>
</article>
</template>

<script setup>
import { ref } from 'vue';
import { useRoute } from 'vue-router';
import InlineSvg from 'vue-inline-svg';
import ToolTipPopup from '@/components/ToolTipPopup'
import { abbreviateUrl, getQueryUrl } from '@/common';

const optsShown = ref('')

function log(m) { console.log(m) }
const props = defineProps({
    data: {type: Object, default: () => {}}
})
const route = useRoute()

function getAuthorUrl(author) {
    return getQueryUrl(route, `author:"${author}"`)
}
function getLastName(author) {
    return author.split(/\s+/).pop()
}
</script>

<style module>
.title em, .snippet em {
    @apply font-bold;
    @apply not-italic;
}

.meta-link:not(:first-child)::before {
    content: '·';
    display: inline-block;
    @apply mx-1.5;
}

.meta-link a {
    @apply text-gray-800;
}

.meta-details {
    a {
        @apply no-underline hover:underline focus:underline;
    }
    dt {
        @apply font-bold text-right;
        @apply float-left w-24 clear-left;
    }

    dd {
        @apply ml-28;
    }
}
</style>
