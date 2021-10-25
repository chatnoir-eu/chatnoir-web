<template>
<span :class="$style['chatnoir-logo']" aria-hidden="true" role="img">
    <object ref="chatNoirLogo" type="image/svg+xml"
            :data="require('@/assets/img/chatnoir.svg').default" @load="init()">
        <img src="@/assets/img/chatnoir.svg" alt="ChatNoir Logo">
    </object>
</span>
</template>

<script setup>
import { ref } from 'vue';

const purrTimeout = ref(null)
const chatNoirLogo = ref(null)

function purr() {
    if (purrTimeout.value !== null) {
        clearTimeout(purrTimeout.value)
    }

    const eyes = chatNoirLogo.value.querySelector('#Eyes')
    eyes.setAttribute('visibility', 'hidden')

    purrTimeout.value = setTimeout(() => {
        eyes.setAttribute('visibility', 'visible')
        purrTimeout.value = null
    }, 300)
}

// Fetch and embed cat as inline SVG to circumvent CORS issues with accessing contentDocument
async function embedCat(element) {
    const result = await fetch(element.getAttribute('data'))
    const tmp = document.createElement('div')
    tmp.innerHTML = await result.text()
    chatNoirLogo.value = tmp.querySelector('svg')
    element.replaceWith(chatNoirLogo.value)
}

function attachEvents() {
    chatNoirLogo.value.querySelector('#Body').addEventListener('mousemove', purr)
}

function init() {
    if (chatNoirLogo.value.tagName.toLowerCase() === 'object') {
        if (chatNoirLogo.value.contentDocument === null) {
            // CORS issue
            embedCat(chatNoirLogo.value).then(() => attachEvents())
            return
        }
        chatNoirLogo.value = chatNoirLogo.value.contentDocument
    }

    attachEvents()
}

defineExpose({
    purr
})
</script>

<style module>
.chatnoir-logo {
    object, svg, img {
        @apply h-40;
        @apply inline-block;
    }
}
</style>
