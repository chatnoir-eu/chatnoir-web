<template>
<span :class="$style['chatnoir-logo']" aria-hidden="true" role="img">
    <object type="image/svg+xml" :data="require('@/assets/img/chatnoir.svg').default" ref="chatnoir-logo" @load="attachEvents()">
        <img src="@/assets/img/chatnoir.svg" alt="ChatNoir Logo">
    </object>
</span>
</template>

<script>
export default {
    data() {
        return {
            purrTimeout: null
        }
    },
    methods: {
        purr() {
            if (this.purrTimeout !== null) {
                clearTimeout(this.purrTimeout)
            }

            let eyes = this.$refs["chatnoir-logo"].contentDocument.querySelector('#Eyes')
            eyes.setAttribute('visibility', 'hidden')

            this.purrTimeout = setTimeout(() => {
                eyes.setAttribute('visibility', 'visible')
                this.purrTimeout = null
            }, 300)
        },
        attachEvents() {
            this.$refs["chatnoir-logo"].contentDocument
                .querySelector('#Body').addEventListener('mousemove', this.purr)
        }
    }
}
</script>

<style module>
.chatnoir-logo {
    object, img {
        @apply h-40;
        @apply inline-block;
    }
}
</style>
