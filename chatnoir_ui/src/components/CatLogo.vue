<template>
<span aria-hidden="true" role="img">
    <router-link v-if="$props.routerTarget" :to="$props.routerTarget">
        <object ref="catLogoElement" class="inline-block h-full max-w-full" :data="logoChatNoir" type="image/svg+xml"></object>
    </router-link>
    <object v-else ref="catLogoElement" class="inline-block h-full max-w-full" :data="logoChatNoir" type="image/svg+xml"></object>
</span>
</template>

<script setup>
import {onMounted, ref} from "vue";
import logoChatNoir from '@/assets/img/chatnoir.svg'
const catLogoElement = ref(null)

import {useRouter} from 'vue-router'

const router = useRouter()

const emit = defineEmits(['purr', 'load', 'click'])

const props = defineProps({
    routerTarget: {type: String, default: null},
})

defineExpose({
    purr: () => {
        if (!catLogoElement.value || !catLogoElement.value.contentDocument) {
            return
        }
        catLogoElement.value.contentDocument.querySelector('#Cat').dispatchEvent(new Event('mousemove'));
        emit('purr', catLogoElement.value.contentDocument)
    }
})

onMounted(() => {
    catLogoElement.value.addEventListener('load', (svg) => {
        if (props.routerTarget) {
            svg.target.contentDocument.firstChild.style.cursor = 'pointer';
        }
        svg.target.contentDocument.addEventListener('click', (e) => {
            if (props.routerTarget) {
                e.preventDefault()
                router.push(props.routerTarget)
            }
            emit('click', e)
        })
    })
})
</script>
