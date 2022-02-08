<!--
    Copyright 2021 Janek Bevendorff

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
-->

<template>
<nav class="text-lg" aria-label="Pagination" role="navigation">
    <a v-for="p in pagesBefore()" :key="p.label" :href="getPageUrl(p.num)" :class="$style['page-button']"
       @click.prevent="navigateToPage(p.num)">
        <!-- eslint-disable-next-line vue/no-v-html -->
        <span v-if="p.icon" v-html="p.icon"></span>
        <span v-else :aria-label="`Page ${p.num}`">{{ p.label }}</span>
    </a>
    <span :class="$style['page-button']" class="text-gray-800 font-bold text-2xl pt-0.5"
          :aria-label="`Page ${page} (Current)`" aria-current="page">
        {{ page }}
    </span>
    <a v-for="p in pagesAfter()" :key="p.label" :href="getPageUrl(p.num)" :class="$style['page-button']"
       @click.prevent="navigateToPage(p.num)">
        <!-- eslint-disable-next-line vue/no-v-html -->
        <span v-if="p.icon" v-html="p.icon"></span>
        <span v-else :aria-label="`Page ${p.num}`">{{ p.label }}</span>
    </a>
</nav>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { buildQueryString } from '@/common'

const router = useRouter()
const route = useRoute()
const showPages = 10

const props = defineProps({
    page: {type: Number, default: 1},
    pageSize: {type: Number, default: 10},
    maxPage: {type: Number, default: 1000},
})
const emit = defineEmits(['update:page'])

const firstIcon = '<img svg-inline src="@/assets/icons/angle-double-left.svg" alt="Go to first page" title="Go to first page" />'
const prevIcon = '<img svg-inline src="@/assets/icons/angle-left.svg" alt="Previous" title="Previous" />'
const nextIcon = '<img svg-inline src="@/assets/icons/angle-right.svg" alt="Next" title="Next" />'

function navigateToPage(p) {
    router.push({query: getPageQuery(p)})
    window.scrollTo(0,0)
    emit('update:page', p)
}

function getPageQuery(p) {
    const params = Object.assign({}, route.query)
    params.p = p
    return params
}

function getPageUrl(p) {
    return route.path + '?' + buildQueryString(getPageQuery(p))
}

function pagesBefore() {
    const pages = []
    if (props.page <= 1) {
        return pages
    }

    let min = Math.max(1, props.page - Math.min(Math.ceil(showPages / 2), props.page) + 1)

    if (min > 1) {
        pages.push({
            icon: firstIcon,
            num: 1
        })
    }

    if (props.page > 1) {
        pages.push({
            icon: prevIcon,
            num: props.page - 1
        })
    }

    for (let i = min; i < props.page; ++i) {
        pages.push({
            label: i.toString(),
            num: i
        })
    }

    return pages
}

function pagesAfter() {
    const pages = []
    if (props.page >= props.maxPage) {
        return pages
    }
    let max = props.page + showPages - Math.min(Math.floor(showPages / 2), props.page)
    max = Math.min(props.maxPage, max)
    for (let i = props.page + 1; i <= max; ++i) {
        pages.push({
            label: i.toString(),
            num: i
        })
    }


    if (props.page < props.maxPage) {
        pages.push({
            icon: nextIcon,
            num: props.page + 1
        })
    }

    return pages
}

</script>

<style module>
.page-button {
    @apply px-2 inline-block align-middle leading-relaxed;

    svg {
        @apply h-5 inline-block -mt-0.5 fill-red;
    }
}
</style>
