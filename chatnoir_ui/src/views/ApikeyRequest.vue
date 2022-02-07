<!--
    Search page view.

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
            <div v-if="$route.name === 'ApikeyRequest_Research'">
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

            <h2 v-if="$route.name === 'ApikeyRequest_Research'" class="text-lg font-bold mt-8 mb-4">API key request form (academic):</h2>
            <form action="" method="post" class="sm:ml-1 mb-20">
                <div class="my-3">
                    <label for="form-name" class="lbl-block lbl-required">Name: *</label>
                    <input id="form-name" ref="formNameField" v-model="formName" type="text" name="name"
                           required placeholder="Please enter your name" class="text-field md:w-1/2 w-full">
                </div>
                <div class="my-3">
                    <label for="form-email" class="lbl-block lbl-required">Email address: *</label>
                    <input id="form-email" v-model="formEmail" type="text" name="email"
                           required placeholder="Email address issued by your institute" class="text-field md:w-1/2 w-full">
                </div>
                <div class="my-3">
                    <label for="form-org" class="lbl-block lbl-required">Organization: *</label>
                    <input id="form-org" v-model="formOrg" type="text" name="org"
                           required placeholder="Academic institute (full name)" class="text-field md:w-1/2 w-full">
                </div>
                <div class="my-3 mt-10">
                    <label for="form-address" class="lbl-block">Postal address (optional):</label>
                    <input id="form-address" v-model="formAddress" type="text" name="address" class="text-field md:w-1/2 w-full">
                </div>
                <div class="my-3">
                    <label for="form-zip" class="lbl-block">ZIP code (optional):</label>
                    <input id="form-zip" v-model="formZip" type="text" name="zip" class="text-field md:w-1/2 w-full">
                </div>
                <div class="my-3">
                    <label for="form-state" class="lbl-block">Federal State (optional):</label>
                    <input id="form-state" v-model="formState" type="text" name="state" class="text-field md:w-1/2 w-full">
                </div>
                <div class="my-3">
                    <label for="form-country" class="lbl-block">Country (optional):</label>
                    <input id="form-country" v-model="formCountry" type="text" name="country" class="text-field md:w-1/2 w-full">
                </div>
                <div v-if="$route.name === 'ApikeyRequest_Research'" class="my-3 mt-10">
                    <label for="form-comment" class="lbl-block lbl-required">What will you use the API key for? *</label>
                    <textarea id="form-comment" v-model="formComment" type="text" name="form-org" maxlength="200"
                              required placeholder="Please give a short description (max. 200 characters)" class="text-field md:w-1/2 w-full"></textarea>
                </div>
                <div v-if="$route.name === 'ApikeyRequest_Research'" class="my-10">
                    <input id="form-agree-tos" v-model="formAgree" type="checkbox" name="agree-tos" required class="chk">
                    <label for="form-agree-tos">
                        I confirm that I will use the API key for <strong>academic purposes only</strong> and agree to the
                        <a href="https://webis.de/legal.html" target="_blank"><strong>Webis Terms of Service</strong></a>.
                    </label>
                </div>
                <div v-if="$route.name === 'ApikeyRequest_Research'" class="my-10">
                    <input type="submit" value="Request Academic API Key" class="btn input-lg primary mr-4">
                    <button class="btn input-lg" @click.prevent="cancelModalState = true">Cancel and Go Back</button>
                </div>
            </form>
<!--            <div class="buttons">-->
<!--                <div class="key-req-tos">-->
<!--                    {{ form.tos_accepted.errors }}-->
<!--                    {{ form.tos_accepted }}-->
<!--                    <label class="form-check-label" for="{{ form.tos_accepted.id_for_label }}" id="KeyReqTosLabel">I agree to the-->
<!--                        <a href="https://www.chatnoir.eu/doc/terms/">ChatNoir Terms of Service</a> *</label>-->
<!--                </div>-->
<!--                <div class="key-req-submit">-->
<!--                    <input class="btn btn-primary" name="submit" type="submit" value="Request Key">-->
<!--                </div>-->
<!--            </div>-->
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
import { onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import SearchHeader from '@/components/SearchHeader'
import ModalDialog from '@/components/ModalDialog'
import { SearchModel } from '@/search-model'

const router = useRouter()
const searchHeaderModel = reactive(new SearchModel())

const formNameField = ref(null)
const cancelModalState = ref(false)
let routeGuardDestination = null

const formName = ref('')
const formEmail = ref('')
const formOrg = ref('')
const formAddress = ref('')
const formZip = ref('')
const formState = ref('')
const formCountry = ref('')
const formComment = ref('')
const formAgree = ref(false)

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
