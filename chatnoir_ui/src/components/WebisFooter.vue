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
<footer class="footer" role="contentinfo" aria-label="Footer">
    <div class="max-w-screen-xl mx-auto p-6 pt-7 sm:flex justify-between text-center sm:text-left">
        <nav class="mb-3 sm:m-0" aria-label="Footer links" role="navigation">
            <span v-for="(item, index) of additionalLinks" :key="item.href">
                <router-link v-if="item.href.fullPath !== undefined" class="group" :to="item.href.fullPath">{{ item.anchor }}</router-link>
                <a v-else class="group" :href="item.href">{{ item.anchor }}</a>
                <span v-if="index !== additionalLinks.length - 1" class="sep">•</span>
            </span>
        </nav>
        <nav aria-label="Contact" role="navigation">
            <span class="group">&copy; {{ (copyrightStartYear ? copyrightStartYear +'&ndash;' : '') + new Date().getFullYear().toString() }} <a href="https://webis.de">Webis Group</a></span>
            <span class="sep">•</span>
            <span class="group">
                <a href="https://github.com/chatnoir-eu"><svg width="15" height="15" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg" role="img"><title>GitHub</title><path d="M10,1 C5.03,1 1,5.03 1,10 C1,13.98 3.58,17.35 7.16,18.54 C7.61,18.62 7.77,18.34 7.77,18.11 C7.77,17.9 7.76,17.33 7.76,16.58 C5.26,17.12 4.73,15.37 4.73,15.37 C4.32,14.33 3.73,14.05 3.73,14.05 C2.91,13.5 3.79,13.5 3.79,13.5 C4.69,13.56 5.17,14.43 5.17,14.43 C5.97,15.8 7.28,15.41 7.79,15.18 C7.87,14.6 8.1,14.2 8.36,13.98 C6.36,13.75 4.26,12.98 4.26,9.53 C4.26,8.55 4.61,7.74 5.19,7.11 C5.1,6.88 4.79,5.97 5.28,4.73 C5.28,4.73 6.04,4.49 7.75,5.65 C8.47,5.45 9.24,5.35 10,5.35 C10.76,5.35 11.53,5.45 12.25,5.65 C13.97,4.48 14.72,4.73 14.72,4.73 C15.21,5.97 14.9,6.88 14.81,7.11 C15.39,7.74 15.73,8.54 15.73,9.53 C15.73,12.99 13.63,13.75 11.62,13.97 C11.94,14.25 12.23,14.8 12.23,15.64 C12.23,16.84 12.22,17.81 12.22,18.11 C12.22,18.35 12.38,18.63 12.84,18.54 C16.42,17.35 19,13.98 19,10 C19,5.03 14.97,1 10,1 L10,1 Z" /></svg></a>
                <a href="https://bsky.app/profile/webis.de"><svg width="15" height="15" role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><title>Bluesky</title><path d="M12 10.8c-1.087-2.114-4.046-6.053-6.798-7.995C2.566.944 1.561 1.266.902 1.565.139 1.908 0 3.08 0 3.768c0 .69.378 5.65.624 6.479.815 2.736 3.713 3.66 6.383 3.364.136-.02.275-.039.415-.056-.138.022-.276.04-.415.056-3.912.58-7.387 2.005-2.83 7.078 5.013 5.19 6.87-1.113 7.823-4.308.953 3.195 2.05 9.271 7.733 4.308 4.267-4.308 1.172-6.498-2.74-7.078a8.741 8.741 0 0 1-.415-.056c.14.017.279.036.415.056 2.67.297 5.568-.628 6.383-3.364.246-.828.624-5.79.624-6.478 0-.69-.139-1.861-.902-2.206-.659-.298-1.664-.62-4.3 1.24C16.046 4.748 13.087 8.687 12 10.8Z" /></svg></a>
                <a href="https://www.youtube.com/webis"><svg width="17" height="17" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg" role="img"><title>YouTube</title><path d="M15,4.1c1,0.1,2.3,0,3,0.8c0.8,0.8,0.9,2.1,0.9,3.1C19,9.2,19,10.9,19,12c-0.1,1.1,0,2.4-0.5,3.4c-0.5,1.1-1.4,1.5-2.5,1.6 c-1.2,0.1-8.6,0.1-11,0c-1.1-0.1-2.4-0.1-3.2-1c-0.7-0.8-0.7-2-0.8-3C1,11.8,1,10.1,1,8.9c0-1.1,0-2.4,0.5-3.4C2,4.5,3,4.3,4.1,4.2 C5.3,4.1,12.6,4,15,4.1z M8,7.5v6l5.5-3L8,7.5z" /></svg></a>
            </span>
            <span class="sep hidden sm:inline">•</span>
            <span class="block mt-3 sm:m-0 sm:inline">
                <a class="group" :href="'https://www.uni-weimar.de/en/media/chairs/computer-science-department/webis/people/' + contactFragment">Contact</a>
                <span class="sep">•</span>
                <a class="group" href="https://webis.de/legal.html">Impressum / Terms / Privacy</a>
            </span>
        </nav>
    </div>
</footer>
</template>

<script setup>
defineProps({
    copyrightStartYear: {type: String, default: ''},
    contactFragment: {type: String, default: ''},
    additionalLinks: {
        type: Array,
        default: () => [],
        validator: (p) => p.every(e => typeof e.href === 'string' && typeof e.anchor === 'string')
    }
})
</script>

<style scoped>
@reference "@/assets/css/index.css";

.footer {
    background: #f7f7f7;
    color: #666;
    font-size: 14px;

    a, a:visited {
        color: inherit;
        @apply no-underline;
        @apply hover:underline;
    }

    .group {
        @apply inline-block;
        @apply mx-2;
    }

    svg {
        fill: #777;
        @apply inline-block;
        @apply mx-1;
        @apply align-middle;
    }

    .sep {
        font-size: .9em;
    }
}
</style>
