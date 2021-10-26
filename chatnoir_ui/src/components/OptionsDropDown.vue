<template>
<div ref="popup" :class="visible ? 'block' : 'hidden'"
     class="bg-gray-100 border border-gray-300 p-5 text-black absolute rounded-lg shadow shadow-lg z-50"
>
    <div class="w-8 overflow-hidden inline-block absolute -top-5 left-1/2 -ml-3">
        <div class="bg-gray-100 border border-gray-300 h-5 w-5 rotate-45 transform origin-bottom-left"></div>
    </div>

    <fieldset>
        <legend class="font-bold mb-1">
            Select Indices:
        </legend>
        <ul class="pl-4">
            <li>
                <input id="select-all" class="chk ml-0" type="checkbox" :checked="allChecked()"
                       @click="toggleAllIndices($event.target.checked)">
                <label for="select-all">(Select All)</label>
            </li>
            <li v-for="(idx, pos) in modelValue" :key="idx.id">
                <input :id="idx.id" name="index" class="chk ml-0" type="checkbox"
                       :checked="idx.selected" :value="idx.id"
                       @click="toggleIndex(pos, $event.target.checked)">
                <label :for="idx.id">{{ idx.name }}</label>
            </li>
        </ul>
    </fieldset>
</div>
</template>

<script setup>
import { onMounted, onUnmounted, ref, toRef, watch } from 'vue';

const emit = defineEmits(['update:modelValue', 'close'])
const props = defineProps({
    modelValue: {type: Object, default: () => {}},
    visible: {type: Boolean, default: false}
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
    const mv = props.modelValue
    for (let idx in mv) {
        mv[idx].selected = on
    }
    emit('update:modelValue', mv)
}

function toggleIndex(pos, on) {
    const mv = props.modelValue
    mv[pos].selected = on
    emit('update:modelValue', mv)
}

function closeOnClick(e) {
    if (popup.value.style.display === 'none') {
        return;
    }
    if (!popup.value.contains(e.target)) {
        emit('close')
        e.stopPropagation()
    }
}

function toggleVisibility(visible) {
    if (visible) {
        document.addEventListener('click', closeOnClick, true)
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

