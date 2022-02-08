<!--
    Search page view.

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
<div class="max-w-full px-5">
    <search-header v-model="searchHeaderModel" @submit="redirectSearch()" />

    <div class="max-w-3xl mx-auto mt-10">
        <h1 class="text-2xl font-bold my-3">Request a ChatNoir API key</h1>

        <div v-if="$route.name === 'ApikeyRequest'">
            <p class="my-3">Purr&hellip; Thank you for your interest in ChatNoir, we are glad to see you here!</p>
            <p class="my-3">
                We offer free API keys for members of verified research institutes. If you qualify for a free API key, you can
                apply by clicking the button below. We will review your request and you will receive your API key by email once approved.
            </p>
            <p class="my-3">
                Alternatively, if you have a ChatNoir passcode, you can use it to issue a (usually time-limited)
                API key immediately.
            </p>

            <div class="my-10 text-center">
                <button class="btn input-xl primary mx-4" @click="$router.push({name: 'ApikeyRequest_Research'})">Apply for a free API key</button>
                <button class="btn input-xl mx-4" @click="$router.push({name: 'ApikeyRequest_Passcode'})">I have a passcode</button>
            </div>
        </div>
        <div v-else-if="$route.name === 'ApikeyRequest_Research' || $route.name === 'ApikeyRequest_Passcode'">
            <div v-if="isAcademic()">
                <p class="my-3">
                    We offer free API keys for members of verified research institutes for academic use.
                </p>
                <p class="my-3">
                    To apply for a free academic API key, please enter your personal details and affiliation below.
                    We will verify your request and you will receive your API key within 1&ndash;2 working days if eligible.
                </p>
                <p class="my-3">
                    If you do not qualify for a free API key or need a key for non-academic purposes, please contact us directly via email,
                    so we can assess your use case and potentially work out an agreement.
                </p>
            </div>

            <h2 v-if="isAcademic()" class="text-lg font-bold mt-8 mb-4">API key request form (academic):</h2>
            <h2 v-else class="text-lg font-bold mt-8 mb-4">API key request form (passcode):</h2>

            <form action="" method="post" novalidate class="sm:ml-1 mb-20" @submit.prevent="submitForm()">
                <form-field v-model="form.name" label="Name" name="name" placeholder="Name which key will be issued to" :validator="v$.name" />

                <form-field v-model="form.email" label="Email address" name="email" type="email"
                            :placeholder="isAcademic() ? 'Email address issued by your institute' : 'Email address for sending the key'"
                            :validator="v$.email" />

                <form-field v-if="isAcademic()" v-model="form.org" label="Organization" name="org"
                            placeholder="Academic institute (full name)" :validator="v$.org" class="my-3 mb-10" />
                <form-field v-else v-model="form.org" label="Organization" name="org" class="my-3 mt-10" />

                <form-field v-model="form.address" label="Postal address" name="address" />
                <form-field v-model="form.zip" label="ZIP code" name="zip" />
                <form-field v-model="form.state" label="Federal State" name="state" />
                <form-field v-model="form.country" label="Country" name="country" />

                <form-field v-if="isAcademic()" v-model="form.comment"
                            label="What will you use the API key for?" name="comment" type="textarea" class="my-3 mt-10"
                            placeholder="Please give a short description (max. 200 characters)"
                            :validator="v$.comment" />

                <form-field v-if="!isAcademic()" v-model="form.passcode" label="Passcode" name="passcode" class="my-3 mt-10"
                            :validator="v$.passcode" />

                <form-field v-model="form.agreeTos" :label-html="agreeTosLabel()" name="agree-tos" type="checkbox"
                            class="mt-10" :validator="v$.agreeTos" />

                <div class="my-10">
                    <input v-if="isAcademic()"
                           type="submit" value="Request Academic API Key" class="btn input-lg primary mr-4">
                    <input v-else type="submit" value="Request API Key" class="btn input-lg primary mr-4">
                    <button class="btn input-lg" @click.prevent="cancelModalState = true">Cancel and Go Back</button>
                </div>
            </form>
        </div>
    </div>

    <modal-dialog v-if="cancelModalState" v-model="cancelModalState" @cancel="cancelModal()">
        <template #header>
            Cancel API key application?
        </template>
        <div class="m-3">
            <p>Do you want to discard all input and cancel the application process?</p>
            <div class="text-center mt-6">
                <button class="btn primary input-lg mx-2" @click.prevent="cancelApplication()">Cancel Application</button>
                <button class="btn input-lg mx-2" @click.prevent="cancelModal()">Go Back To Form</button>
            </div>
        </div>
    </modal-dialog>
</div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import useVuelidate from '@vuelidate/core'
import { email, helpers, required, sameAs } from '@vuelidate/validators'

import SearchHeader from '@/components/SearchHeader'
import ModalDialog from '@/components/ModalDialog'
import { SearchModel } from '@/search-model'
import FormField from '@/components/FormField'

const router = useRouter()
const route = useRoute()
const searchHeaderModel = reactive(new SearchModel())

const formNameField = ref(null)
const cancelModalState = ref(false)
let routeGuardDestination = null

const form = reactive({
    name: '',
    email: '',
    org: '',
    address: '',
    zip: '',
    state: '',
    country: '',
    comment: '',
    passcode: '',
    agreeTos: false
})

const rules = {
    name: { required },
    email: { required, email },
    org: { required },
    comment: { required },
    passcode: { required },
    agreeTos: { required: helpers.withMessage('You must accept the Terms of Service', sameAs(true)) },
}

const v$ = useVuelidate(rules, form)


function isAcademic() {
    return route.name === 'ApikeyRequest_Research'
}

function agreeTosLabel() {
    if (isAcademic()) {
        return 'I confirm that I will use the API key for <strong>academic purposes only</strong> and agree to the ' +
            '<a href="https://webis.de/legal.html" target="_blank"><strong>Webis Terms of Service</strong></a>'
    }
    return 'By requesting an API key, I agree to the <a href="https://webis.de/legal.html" target="_blank"><strong>Webis Terms of Service</strong></a>'
}

function submitForm() {
    v$.value.$validate()
    console.log(v$.value.name)
}

function redirectSearch() {
    router.push({name: 'IndexSearch', query: searchHeaderModel.toQueryString()})
}

function cancelApplication() {
    cancelModalState.value = false
    if (routeGuardDestination === null) {
        routeGuardDestination = {name: 'ApikeyRequest'}
    }
    router.push(routeGuardDestination)
}

function cancelModal() {
    routeGuardDestination = null
    cancelModalState.value = false
}

onMounted(() => {
    if (formNameField.value) {
        formNameField.value.focus()
    }
    routeGuardDestination = null
})

router.beforeEach((to, from) => {
    // Request form route, guard with modal
    if (from.name === 'ApikeyRequest_Research' || from.name === 'ApikeyRequest_Passcode') {
        if (routeGuardDestination === null) {
            routeGuardDestination = to
            cancelModalState.value = true
            return false
        }
    }

    // Not a request form route or modal has been shown and confirmed by the user
    routeGuardDestination = to
    return true
})
</script>
