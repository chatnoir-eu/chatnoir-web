<template>
<span aria-hidden="true" role="img">
    <inline-svg class="inline-block h-full w-auto max-w-full"
                :src="require('@/assets/img/chatnoir.svg').default" @loaded="logoElement = $event" />
</span>
</template>

<script setup>
import { ref, watch } from 'vue';

const purrTimeout = ref(null)
const logoElement = ref(null)

function purr() {
    if (!logoElement.value) {
        return
    }
    if (purrTimeout.value !== null) {
        clearTimeout(purrTimeout.value)
    }

    const eyes = logoElement.value.querySelector('#Eyes')
    eyes.setAttribute('visibility', 'hidden')

    purrTimeout.value = setTimeout(() => {
        eyes.setAttribute('visibility', 'visible')
        purrTimeout.value = null
    }, 300)
}

watch(logoElement, () => {
    logoElement.value.querySelector('#Body').addEventListener('mousemove', purr)
})

defineExpose({
    purr
})
</script>
