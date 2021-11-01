<template>
<div ref="popup" class="tooltip-popup invisible hidden w-max transform">
    <div class="py-1 px-1.5">
        <slot />
    </div>
</div>
</template>

<script setup>
import { onMounted, onUnmounted, ref, toRef, watch } from 'vue'
import { rem2Px } from '@/common'

const emit = defineEmits(['close'])
const props = defineProps({
    visible: {type: Boolean, default: false},
    refElement: {type: Object, default: null}
})
const popup = ref(null)

function closeOnClick(e) {
    if (!popup.value || popup.value.style.display === 'none') {
        return
    }
    if (!popup.value.contains(e.target)) {
        emit('close')
        e.stopPropagation()
    }
}

function toggleVisibility(visible) {
    if (!popup.value) {
        return
    }

    const animationClasses = ['opacity-0', 'invisible', '-translate-y-3']
    popup.value.classList.add(...animationClasses)

    if (visible) {
        document.addEventListener('click', closeOnClick, true)
        popup.value.classList.remove('invisible', 'hidden')

        const tailOffset = rem2Px(1.3)

        // Align offset with reference element
        if (props.refElement) {
            let left = props.refElement.offsetLeft - (popup.value.clientWidth - props.refElement.clientWidth) / 2
            let top = props.refElement.offsetTop + props.refElement.offsetHeight + tailOffset

            // flip popup if scroll / document height insufficient
            let refBr = props.refElement.getBoundingClientRect()
            if (refBr.top + popup.value.offsetHeight + tailOffset > window.innerHeight
                && refBr.top >= popup.value.offsetHeight + tailOffset) {
                top = props.refElement.offsetTop - popup.value.offsetHeight - tailOffset

                if (popup.value.classList.contains('tail-top')) {
                    popup.value.classList.remove('tail-top')
                    popup.value.classList.add('tail-bottom')
                }
            } else if (popup.value.classList.contains('tail-bottom')) {
                popup.value.classList.remove('tail-bottom')
                popup.value.classList.add('tail-top')
            }

            popup.value.style.left = `${left}px`
            popup.value.style.top = `${top}px`
            popup.value.style.transition = 'opacity 400ms, visibility 400ms, transform 400ms'
            popup.value.classList.remove(...animationClasses)
        }
    } else {
        document.removeEventListener('click', closeOnClick, true)
    }
}

watch(toRef(props, 'visible'), (newValue, prevValue) => {
    if (newValue === prevValue) {
        return
    }
    toggleVisibility(newValue)
})

onMounted(() => {
    toggleVisibility(props.visible)
})

onUnmounted(() => {
    toggleVisibility(false)
})
</script>

<style>
.tooltip-popup {
    @apply absolute z-50;
    @apply bg-gray-100;
    @apply border border-gray-300 rounded-sm;
    @apply p-4;
    @apply text-black;
    @apply shadow shadow-lg;
    @apply ease-in-out;

    &::after, &::before {
        @apply absolute;
        @apply border-transparent;
        border-width: 1rem;
        content: '';
    }

    &:before {
        border-width: calc(1rem + theme('borderWidth.DEFAULT'));
    }

    &.tail-bottom::after, &.tail-bottom::before {
        border-top-color: theme('colors.gray.100');
        border-bottom: 0;
        left: 50%;
        bottom: calc(-1rem + theme('borderWidth.DEFAULT'));
        margin-left: -1rem;
    }

    &.tail-bottom::before {
        border-top-color: theme('colors.gray.300');
        bottom: calc(-1rem - theme('borderWidth.DEFAULT'));
        margin-left: calc(-1rem - theme('borderWidth.DEFAULT'));
    }

    &.tail-top::after, &.tail-top::before {
        border-bottom-color: theme('colors.gray.100');
        border-top: 0;
        left: 50%;
        top: calc(-1rem + theme('borderWidth.DEFAULT'));
        margin-left: -1rem;
    }

    &.tail-top::before {
        border-bottom-color: theme('colors.gray.300');
        top: calc(-1rem - theme('borderWidth.DEFAULT'));
        margin-left: calc(-1rem - theme('borderWidth.DEFAULT'));
    }

    &.tail-left::after, &.tail-left::before {
        border-right-color: theme('colors.gray.100');
        border-left: 0;
        left: calc(-1rem + theme('borderWidth.DEFAULT'));
        top: 50%;
        margin-top: -1rem;
    }

    &.tail-left::before {
        border-right-color: theme('colors.gray.300');
        left: calc(-1rem - theme('borderWidth.DEFAULT'));
        margin-top: calc(-1rem - theme('borderWidth.DEFAULT'));
    }

    &.tail-right::after, &.tail-right::before {
        border-left-color: theme('colors.gray.100');
        border-right: 0;
        right: -1rem;
        top: 50%;
        margin-top: -1rem;
    }

    &.tail-right::before {
        border-left-color: theme('colors.gray.300');
        right: calc(-1rem - theme('borderWidth.DEFAULT'));
        margin-top: calc(-1rem - theme('borderWidth.DEFAULT'));
    }
}
</style>
