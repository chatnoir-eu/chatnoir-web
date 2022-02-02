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
<search-header v-model="searchHeaderModel" @submit="redirectSearch()" />
        <div id="Main" class="container">
        {% include 'search_frontend/include/search-header.html' %}

        <section id="ApiKeyContent">
            <h1>Welcome!</h1>
            <p>Purr... We are glad to see you here.</p>
            <p>If you have a valid ChatNoir passcode, you can use the form below to request your personal
            ChatNoir API key.</p>

            <h2>Request API Key</h2>
            <p>To receive an API key, please fill in the following information. Fields marked with <strong>*</strong>
            are required.</p>
<!--            {{ form.non_field_errors }}-->
<!--            <form action="{% url 'apikey_management:index' %}" method="post" id="ApiKeyReqForm">-->
<!--                <div class="main-fields">-->
<!--                    <div class="key-req-name">-->
<!--                        {{ form.common_name.errors }}-->
<!--                        <label for="{ form.common_name.id_for_label }">Name: *</label>-->
<!--                        {{ form.common_name }}-->
<!--                    </div>-->
<!--                    <div class="key-req-email">-->
<!--                        {{ form.email.errors }}-->
<!--                        <label for="{{ form.email.id_for_label }}">Email address: *</label>-->
<!--                        {{ form.email }}-->
<!--                    </div>-->
<!--                    <div class="key-req-org">-->
<!--                        {{ form.organization.errors }}-->
<!--                        <label for="{{ form.organization.id_for_label }}">Organization:</label>-->
<!--                        {{ form.organization }}-->
<!--                    </div>-->
<!--                    <div class="key-req-address">-->
<!--                        {{ form.address.errors }}-->
<!--                        <label for="{{ form.address.id_for_label }}">Postal address:</label>-->
<!--                        {{ form.address }}-->
<!--                    </div>-->
<!--                    <div class="key-req-zipcode">-->
<!--                        {{ form.zip_code.errors }}-->
<!--                        <label for="{{ form.zip_code.id_for_label }}">ZIP code:</label>-->
<!--                        {{ form.zip_code }}-->
<!--                    </div>-->
<!--                    <div class="key-req-state">-->
<!--                        {{ form.state.errors }}-->
<!--                        <label for="{{ form.state.id_for_label }}">State:</label>-->
<!--                        {{ form.state }}-->
<!--                    </div>-->
<!--                    <div class="key-req-country">-->
<!--                        {{ form.country.errors }}-->
<!--                        <label for="{{ form.country.id_for_label }}">Country:</label>-->
<!--                        {{ form.country }}-->
<!--                    </div>-->
<!--                    <div class="key-req-passcode">-->
<!--                        {{ form.passcode.errors }}-->
<!--                        <label for="{{ form.passcode.id_for_label }}">Passcode: *</label>-->
<!--                        {{ form.passcode }}-->
<!--                    </div>-->
<!--                </div>-->
<!--                <div class="buttons">-->
<!--                    <div class="key-req-tos">-->
<!--                        {{ form.tos_accepted.errors }}-->
<!--                        {{ form.tos_accepted }}-->
<!--                        <label class="form-check-label" for="{{ form.tos_accepted.id_for_label }}" id="KeyReqTosLabel">I agree to the-->
<!--                            <a href="https://www.chatnoir.eu/doc/terms/">ChatNoir Terms of Service</a> *</label>-->
<!--                    </div>-->
<!--                    <div class="key-req-submit">-->
<!--                        <input class="btn btn-primary" name="submit" type="submit" value="Request Key">-->
<!--                    </div>-->
<!--                </div>-->
<!--                <div>{% csrf_token %} </div>-->
<!--            </form>-->
        </section>
    </div>

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
