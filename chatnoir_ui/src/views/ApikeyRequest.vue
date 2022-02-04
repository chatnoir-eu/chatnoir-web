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
                <button class="btn primary" @click="$router.push({name: 'ApikeyRequest_Research'})">Apply for a free API key</button>
                <button class="btn" @click="$router.push({name: 'ApikeyRequest_Passcode'})">I have a passcode</button>
            </div>
        </div>
        <div v-else-if="$route.name === 'ApikeyRequest_Research'">
            <p class="my-3">Research</p>
        </div>
        <div v-else-if="$route.name === 'ApikeyRequest_Passcode'">
            <p class="my-3">Passcode</p>
        </div>
    </div>
</div>
    <!--        <h2>Request API Key</h2>-->
    <!--        <p>-->
    <!--            To receive an API key, please fill in the following information. Fields marked with <strong>*</strong>-->
    <!--        are required.</p>-->
    <!--&lt;!&ndash;            {{ form.non_field_errors }}&ndash;&gt;-->
    <!--&lt;!&ndash;            <form action="{% url 'apikey_management:index' %}" method="post" id="ApiKeyReqForm">&ndash;&gt;-->
    <!--&lt;!&ndash;                <div class="main-fields">&ndash;&gt;-->
    <!--&lt;!&ndash;                    <div class="key-req-name">&ndash;&gt;-->
    <!--&lt;!&ndash;                        {{ form.common_name.errors }}&ndash;&gt;-->
    <!--&lt;!&ndash;                        <label for="{ form.common_name.id_for_label }">Name: *</label>&ndash;&gt;-->
    <!--&lt;!&ndash;                        {{ form.common_name }}&ndash;&gt;-->
    <!--&lt;!&ndash;                    </div>&ndash;&gt;-->
    <!--&lt;!&ndash;                    <div class="key-req-email">&ndash;&gt;-->
    <!--&lt;!&ndash;                        {{ form.email.errors }}&ndash;&gt;-->
    <!--&lt;!&ndash;                        <label for="{{ form.email.id_for_label }}">Email address: *</label>&ndash;&gt;-->
    <!--&lt;!&ndash;                        {{ form.email }}&ndash;&gt;-->
    <!--&lt;!&ndash;                    </div>&ndash;&gt;-->
    <!--&lt;!&ndash;                    <div class="key-req-org">&ndash;&gt;-->
    <!--&lt;!&ndash;                        {{ form.organization.errors }}&ndash;&gt;-->
    <!--&lt;!&ndash;                        <label for="{{ form.organization.id_for_label }}">Organization:</label>&ndash;&gt;-->
    <!--&lt;!&ndash;                        {{ form.organization }}&ndash;&gt;-->
    <!--&lt;!&ndash;                    </div>&ndash;&gt;-->
    <!--&lt;!&ndash;                    <div class="key-req-address">&ndash;&gt;-->
    <!--&lt;!&ndash;                        {{ form.address.errors }}&ndash;&gt;-->
    <!--&lt;!&ndash;                        <label for="{{ form.address.id_for_label }}">Postal address:</label>&ndash;&gt;-->
    <!--&lt;!&ndash;                        {{ form.address }}&ndash;&gt;-->
    <!--&lt;!&ndash;                    </div>&ndash;&gt;-->
    <!--&lt;!&ndash;                    <div class="key-req-zipcode">&ndash;&gt;-->
    <!--&lt;!&ndash;                        {{ form.zip_code.errors }}&ndash;&gt;-->
    <!--&lt;!&ndash;                        <label for="{{ form.zip_code.id_for_label }}">ZIP code:</label>&ndash;&gt;-->
    <!--&lt;!&ndash;                        {{ form.zip_code }}&ndash;&gt;-->
    <!--&lt;!&ndash;                    </div>&ndash;&gt;-->
    <!--&lt;!&ndash;                    <div class="key-req-state">&ndash;&gt;-->
    <!--&lt;!&ndash;                        {{ form.state.errors }}&ndash;&gt;-->
    <!--&lt;!&ndash;                        <label for="{{ form.state.id_for_label }}">State:</label>&ndash;&gt;-->
    <!--&lt;!&ndash;                        {{ form.state }}&ndash;&gt;-->
    <!--&lt;!&ndash;                    </div>&ndash;&gt;-->
    <!--&lt;!&ndash;                    <div class="key-req-country">&ndash;&gt;-->
    <!--&lt;!&ndash;                        {{ form.country.errors }}&ndash;&gt;-->
    <!--&lt;!&ndash;                        <label for="{{ form.country.id_for_label }}">Country:</label>&ndash;&gt;-->
    <!--&lt;!&ndash;                        {{ form.country }}&ndash;&gt;-->
    <!--&lt;!&ndash;                    </div>&ndash;&gt;-->
    <!--&lt;!&ndash;                    <div class="key-req-passcode">&ndash;&gt;-->
    <!--&lt;!&ndash;                        {{ form.passcode.errors }}&ndash;&gt;-->
    <!--&lt;!&ndash;                        <label for="{{ form.passcode.id_for_label }}">Passcode: *</label>&ndash;&gt;-->
    <!--&lt;!&ndash;                        {{ form.passcode }}&ndash;&gt;-->
    <!--&lt;!&ndash;                    </div>&ndash;&gt;-->
    <!--&lt;!&ndash;                </div>&ndash;&gt;-->
    <!--&lt;!&ndash;                <div class="buttons">&ndash;&gt;-->
    <!--&lt;!&ndash;                    <div class="key-req-tos">&ndash;&gt;-->
    <!--&lt;!&ndash;                        {{ form.tos_accepted.errors }}&ndash;&gt;-->
    <!--&lt;!&ndash;                        {{ form.tos_accepted }}&ndash;&gt;-->
    <!--&lt;!&ndash;                        <label class="form-check-label" for="{{ form.tos_accepted.id_for_label }}" id="KeyReqTosLabel">I agree to the&ndash;&gt;-->
    <!--&lt;!&ndash;                            <a href="https://www.chatnoir.eu/doc/terms/">ChatNoir Terms of Service</a> *</label>&ndash;&gt;-->
    <!--&lt;!&ndash;                    </div>&ndash;&gt;-->
    <!--&lt;!&ndash;                    <div class="key-req-submit">&ndash;&gt;-->
    <!--&lt;!&ndash;                        <input class="btn btn-primary" name="submit" type="submit" value="Request Key">&ndash;&gt;-->
    <!--&lt;!&ndash;                    </div>&ndash;&gt;-->
    <!--&lt;!&ndash;                </div>&ndash;&gt;-->
    <!--&lt;!&ndash;                <div>{% csrf_token %} </div>&ndash;&gt;-->
    <!--&lt;!&ndash;            </form>&ndash;&gt;-->
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { searchModelToQueryString } from '@/common'

import SearchHeader from '@/components/SearchHeader'

const router = useRouter()
const searchHeaderModel = ref({})


function redirectSearch() {
    router.push({name: 'IndexSearch', query: searchModelToQueryString(searchHeaderModel.value)})
}
</script>
