<template>
<div ref="popup" class="popup tail-top invisible w-max transform">
    <fieldset>
        <legend class="font-bold mb-1.5">
            Select Indices:
        </legend>
        <ul class="pl-3 pb-1">
            <li class="pb-0.5">
                <input id="select-all" class="chk ml-0" type="checkbox" :checked="allChecked()"
                       @click="toggleAllIndices($event.target.checked)">
                <label for="select-all">(Select All)</label>
            </li>
            <li v-for="(idx, pos) in modelValue" :key="idx.id" class="pb-0.5">
                <input :id="idx.id" name="index" class="chk ml-0 pb-1" type="checkbox"
                       :checked="idx.selected" :value="idx.id"
                       @click="toggleIndex(pos, $event.target.checked)">
                <label :for="idx.id">{{ idx.name }}</label>
            </li>
        </ul>
    </fieldset>
</div>
</template>

<script setup>
import { onMounted, onUnmounted, ref, toRef, unref, watch } from 'vue';

const emit = defineEmits(['update:modelValue', 'close'])
const props = defineProps({
    modelValue: {type: Array, default: () => []},
    visible: {type: Boolean, default: false},
    refElement: {type: Object, default: null}
})
const popup = ref(null)

function allChecked() {
    for (let idx in props.modelValue) {
        if (!props.modelValue[idx].selected) {
            return false
        }
    }
    return true
}

function toggleAllIndices(on) {
    const mv = Array.from(props.modelValue)
    for (let idx in mv) {
        mv[idx].selected = on
    }
    emit('update:modelValue', mv)
}

function toggleIndex(pos, on) {
    const mv = Array.from(props.modelValue)
    mv[pos].selected = on
    emit('update:modelValue', mv)
}

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

        // Align offset with reference element
        if (props.refElement) {
            popup.value.style.left = `${props.refElement.offsetLeft - popup.value.clientWidth / 2 + 1}px`
            popup.value.style.top = `calc(${props.refElement.offsetTop + props.refElement.offsetHeight}px + 1.3rem)`

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
