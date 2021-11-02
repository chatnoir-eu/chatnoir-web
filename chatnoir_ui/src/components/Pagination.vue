<template>
<div>
    <a v-for="p in pagesBefore()" :key="p.label" :href="getPageUrl(p.num)" class="px-2 h-4 inline-block align-middle"
       @click.prevent="navigateToPage(p.num)">
        <inline-svg v-if="p.icon" :src="p.icon" :arial-label="p.label" :title="p.label" class="h-full inline-block -mt-1" />
        <span v-else>{{ p.label }}</span>
    </a>
    <span class="px-2 h-4 inline-block align-middle">{{ modelValue.page }}</span>
    <a v-for="p in pagesAfter()" :key="p.label" :href="getPageUrl(p.num)" class="px-2 h-4 inline-block align-middle"
       @click.prevent="navigateToPage(p.num)">
        <inline-svg v-if="p.icon" :src="p.icon" :arial-label="p.label" :title="p.label" class="h-full inline-block -mt-1" />
        <span v-else>{{ p.label }}</span>
    </a>
</div>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { buildQueryString } from '@/common'

const router = useRouter()
const route = useRoute()
const showPages = 10

const props = defineProps({
    modelValue: {
        type: Object,
        default: () => {
            return {
                page: 1,
                maxPage: 1,
                paginationSize: 10
            }
        },
        validator(v) {
            return v.page !== undefined && v.maxPage !== undefined && v.paginationSize && v.paginationSize > 0
        }
    }
})

function navigateToPage(p) {
    router.push({query: getPageQuery(p)})
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
    const p = props.modelValue
    const pages = []
    if (p.page <= 1) {
        return pages
    }

    let min = Math.max(1, p.page - Math.min(Math.ceil(showPages / 2), p.page) + 1)

    if (min > 1) {
        pages.push({
            label: 'Go to first page',
            icon: require('@/assets/icons/angle-double-left.svg').default,
            num: 1
        })
    }

    if (p.page > 1) {
        pages.push({
            label: 'Previous',
            icon: require('@/assets/icons/angle-left.svg').default,
            num: p.page - 1
        })
    }

    for (let i = min; i < p.page; ++i) {
        pages.push({
            label: i.toString(),
            icon: null,
            num: i
        })
    }

    return pages
}

function pagesAfter() {
    const p = props.modelValue
    const pages = []
    if (p.page >= p.maxPage) {
        return pages
    }
    let max = p.page + showPages - Math.min(Math.floor(showPages / 2), p.page)
    max = Math.min(p.maxPage, max)
    for (let i = p.page + 1; i <= max; ++i) {
        pages.push({
            label: i.toString(),
            icon: null,
            num: i
        })
    }


    if (p.page < p.maxPage) {
        pages.push({
            label: 'Next',
            icon: require('@/assets/icons/angle-right.svg').default,
            num: p.page + 1
        })
    }

    return pages
}
</script>
