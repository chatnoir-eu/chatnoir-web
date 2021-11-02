<template>
<div ref="mainElement" class="h-0.5 w-full m-0 p-0 invisible overflow-hidden" aria-hidden="true">
    <div class="h-full m-0 p-0 bg-red-400 rounded-r-full transition-width duration-150" :style="`width: ${displayedProgress}%`"></div>
</div>
</template>

<script setup>
import { onMounted, ref, toRef, watch } from 'vue'

const emit = defineEmits(['complete'])
const props = defineProps({
    progress: {type: Number, default: 0}
})
const mainElement = ref(null)
const displayedProgress = ref(0)

function updateProgress() {
    if (props.progress > 0) {
        mainElement.value.classList.remove('invisible')
    }

    displayedProgress.value = Math.max(0, displayedProgress.value + (props.progress - displayedProgress.value) / 2)
    setTimeout(() => {
        displayedProgress.value = props.progress
    }, 100)

    if (props.progress >= 100) {
        setTimeout(() => {
            mainElement.value.classList.add('invisible')
            displayedProgress.value = 0
            emit('complete')
        }, 200)
    }
}

watch(toRef(props, 'progress'), () => {
    updateProgress()
})

onMounted(() => {
    updateProgress()
})
</script>
