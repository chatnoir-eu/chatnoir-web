<template>
<span ref="chatNoirLogoContainer" :class="$style['chatnoir-logo']" aria-hidden="true" role="img">
    <inline-svg :src="require('@/assets/img/chatnoir.svg').default" @loaded="logoElement = $event" />
</span>
</template>

<script setup>
import { ref, watch } from 'vue';
import InlineSvg from 'vue-inline-svg';

const purrTimeout = ref(null)
const logoElement = ref(null)

function purr() {
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

<style module>
.chatnoir-logo {
    object, svg, img {
        @apply inline-block;
        @apply h-full w-auto max-w-full;
    }
}
</style>
