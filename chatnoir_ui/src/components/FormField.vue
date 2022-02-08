<!--
    Copyright 2022 Janek Bevendorff

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
<div v-if="isTextField()" :class="$props.class">
    <label v-if="$props.label || $props.labelHtml" :for="'form-' + $props.name" class="lbl-block" :class="labelCls()">
        <!-- eslint-disable-next-line vue/no-v-html -->
        <span v-if="$props.labelHtml" v-html="$props.labelHtml"></span><span v-else>{{ $props.label }}</span>
        <span v-if="!isValid()"> ({{ errors() }})</span>
        <span v-if="isRequired()"> *</span><span v-else> (optional)</span>
    </label>
    <input v-if="$props.type !== 'textarea'"
           :id="'form-' + $props.name"
           v-model="model"
           :type="$props.type"
           :name="$props.name"
           :required="isRequired()"
           :placeholder="$props.placeholder"
           class="text-field md:w-1/2 w-full" :class="inputCls()"
           v-bind="$attrs"
           @blur="touch()">
    <textarea v-else
              :id="'form-' + $props.name"
              v-model="model"
              :name="$props.name"
              :required="isRequired()"
              :placeholder="$props.placeholder"
              class="text-field md:w-1/2 w-full" :class="inputCls()"
              v-bind="$attrs"
              @blur="touch()"></textarea>
</div>
<div v-else :class="$props.class">
    <div v-if="!isValid()" class="form-error text-sm">{{ errors() }}</div>
    <input v-if="$props.type !== 'textarea'"
           :id="'form-' + $props.name"
           v-model="model"
           :type="$props.type"
           :name="$props.name"
           :required="isRequired()"
           :class="inputCls()"
           v-bind="$attrs">
    <label v-if="$props.label || $props.labelHtml" :for="'form-' + $props.name">
        <!-- eslint-disable-next-line vue/no-v-html -->
        <span v-if="$props.labelHtml" v-html="$props.labelHtml"></span><span v-else>{{ $props.label }}</span>
        <span v-if="isRequired()"> *</span>
    </label>
</div>
</template>

<script>
export default {
    inheritAttrs: false
}
</script>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
    modelValue: {},
    type: {type: String, default: 'text'},
    name: {type: String, required: true},
    placeholder: {type: String},
    label: {type: String},
    labelHtml: {type: String},
    class: {type: String, default: 'my-3'},
    validator: {type: Object, default: null},
})
const model = ref(null)

const emit = defineEmits(['update:modelValue'])
watch(model, (newValue) => {
    emit('update:modelValue', newValue)
})

function isTextField() {
    return props.type !== 'checkbox' && props.type !== 'radio'
}

function isValid() {
    if (!props.validator) {
        return true
    }
    return props.validator.$errors.length === 0
}

function isRequired() {
    return props.validator && props.validator.required
}

function errors() {
    if (!props.validator) {
        return ''
    }
    return props.validator.$errors.map((e) => e.$message).join(', ')
}

function labelCls() {
    const cls = []
    if (isRequired()) {
        cls.push('lbl-required')
    }
    if (props.validator && !isValid(props.validator)) {
        cls.push('form-error')
    }
    return cls.join(' ')
}

function inputCls() {
    if (props.type === 'checkbox') {
        return 'chk'
    }
    if (props.type === 'radio') {
        return 'radio'
    }
    if (props.validator && !isValid(props.validator)) {
        return 'invalid'
    }
    return ''
}

function touch() {
    if (props.validator) {
        props.validator.$touch()
    }
}
</script>
