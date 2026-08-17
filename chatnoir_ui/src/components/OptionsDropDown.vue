<!--
    Copyright 2021 Janek Bevendorff

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
-->

<template>
<ToolTipPopup v-bind="attrs" class="tail-top">
    <fieldset>
        <legend class="font-bold mb-2">
            Select Indices:
        </legend>
        <ul class="pl-2">
            <li class="pb-0.5">
                <input id="select-all" class="chk ml-0" type="checkbox" :checked="allChecked()"
                       @click="toggleAllIndices($event.target.checked)">
                <label for="select-all">(Select All)</label>
            </li>
            <li v-for="(idx, pos) in modelValue" :key="idx.id" class="pb-0.5">
                <input :id="idx.id" name="index" class="chk ml-0 pb-1" type="checkbox"
                       :checked="idx.selected && !idx.restricted" :value="idx.id"
                       :disabled="idx.restricted"
                       @click="toggleIndex(pos, $event.target.checked)">
                <label :for="idx.id">
                    {{ idx.name }}
                    <span v-if="idx.restricted"
                          class="inline-block"
                          title="Restricted Index: Enter API key or contact us for access">
                        <inline-svg
                            :src="iconInfo"
                            class="inline-block h-[1em] w-[1em] align-text-middle text-inherit fill-current stroke-current cursor-help"
                        />
                    </span>
                </label>
            </li>
        </ul>
    </fieldset>
    <fieldset class="mt-2">
        <legend class="font-bold mb-2">
            <span v-if="apiKeyUserName">User Info:</span>
            <span v-else>Enter API Key:</span>
        </legend>
        <div v-if="apiKeyUserName" class="space-y-2">
            <div>Logged in as: {{ apiKeyUserName }}</div>
            <button type="button" class="btn mt-1" @click="logoutApiKey">Logout</button>
        </div>
        <div v-else class="space-y-2">
            <input
                v-model="apiKey"
                class="text-field w-full m-0"
                type="password"
                placeholder="API key"
                autocomplete="off"
                @keyup.enter="saveApiKey"
            >
            <div class="flex items-center gap-2 mt-1">
                <button type="button" class="btn" :disabled="apiKeySaving || !apiKey.trim()" @click="saveApiKey">
                    Log in
                </button>
                <span v-if="apiKeyError" class="text-red-600">{{ apiKeyError }}</span>
            </div>
        </div>
    </fieldset>
</ToolTipPopup>
</template>

<script setup>
import { onMounted, ref, useAttrs } from 'vue'
import ToolTipPopup from '@/components/ToolTipPopup.vue'
import iconInfo from '@/assets/icons/info.svg'
import { clearStoredApiKey, getStoredApiUserName, refreshAvailableIndices, storeApiKey } from '@/search-model.mjs'

defineOptions({inheritAttrs: false})

const emit = defineEmits(['update:modelValue'])
const props = defineProps({
    modelValue: {type: Array, default: () => []}
})
const attrs = useAttrs()
const apiKey = ref('')
const apiKeyUserName = ref(null)
const apiKeyError = ref('')
const apiKeySaving = ref(false)

onMounted(() => {
    apiKeyUserName.value = getStoredApiUserName()
})

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

async function saveApiKey() {
    const trimmedApiKey = apiKey.value.trim()
    if (!trimmedApiKey || apiKeySaving.value) {
        return
    }

    apiKeySaving.value = true
    apiKeyError.value = ''

    try {
        apiKeyUserName.value = await storeApiKey(trimmedApiKey)
        emit('update:modelValue', await refreshIndexOptions())
        apiKey.value = ''
    } catch {
        apiKeyError.value = 'Invalid API key.'
    } finally {
        apiKeySaving.value = false
    }
}

function logoutApiKey() {
    clearStoredApiKey()
    apiKey.value = ''
    apiKeyUserName.value = null
    apiKeyError.value = ''
    refreshIndexOptions().then((indices) => emit('update:modelValue', indices))
}

async function refreshIndexOptions() {
    return await refreshAvailableIndices(props.modelValue.filter((idx) => idx.selected).map((idx) => idx.id))
}
</script>
