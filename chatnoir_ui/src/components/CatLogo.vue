<template>
<span :class="$style['chatnoir-logo']" aria-hidden="true" role="img">
    <object type="image/svg+xml" :data="require('@/assets/img/chatnoir.svg').default" @mouseenter="purr()" @mouseout="purr(false)" ref="chatnoir-logo">
        <img src="@/assets/img/chatnoir.svg" alt="ChatNoir Logo">
    </object>
</span>
</template>

<script>
export default {
    methods: {
        purr(state) {
            let eyes = this.$refs["chatnoir-logo"].contentDocument.querySelector('#Eyes')
            eyes.setAttribute('visibility', state === false ? 'visible' : 'hidden')
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
