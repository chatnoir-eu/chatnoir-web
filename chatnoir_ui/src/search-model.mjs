/*
 * Copyright 2021 Janek Bevendorff
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */


import { Mutex } from 'async-mutex'
import { objSnake2Camel, objCamelToSnake } from '@/common.mjs'
import xhr from '@/xhr.mjs'


const GLOBAL_STATE = {
    apiToken: null,
    indices: [],
    counter: -1,
    mutex: new Mutex()
}

/**
 * Request new temporary API tokens.
 */
export async function refreshGlobalState() {
    await GLOBAL_STATE.mutex.runExclusive(async () => {
        if (GLOBAL_STATE.apiToken !== null
            && Date.now() / 1000 - GLOBAL_STATE.apiToken.timestamp < GLOBAL_STATE.apiToken.maxAge - 20
            && GLOBAL_STATE.counter < GLOBAL_STATE.apiToken.quota) {
            return
        }

        const response = await xhr({
            method: 'POST',
            url: import.meta.env.VITE_BACKEND_ADDRESS + '?init',
            withCredentials: true,
            withXSRFToken: true,
        }).catch((e) => {
            throw new Error('Invalid state returned. ' + e)
        })

        GLOBAL_STATE.apiToken = ApiToken.fromJSON(response.data.token)
        GLOBAL_STATE.indices = IndexDesc.fromJSON(response.data.indices)
        GLOBAL_STATE.counter = 0
    })
    return GLOBAL_STATE
}

/**
 * Request token data class.
 */
export class ApiToken {
    constructor({token, timestamp, maxAge, quota}) {
        this.token = token
        this.timestamp = timestamp
        this.maxAge = maxAge
        this.quota = quota
    }

    static fromJSON(jsonData) {
        return new ApiToken(objSnake2Camel(jsonData))
    }
}

/**
 * Index meta descriptor.
 */
export class IndexDesc {
    constructor({id, name, selected}) {
        this.id = id
        this.name = name
        this.selected = selected || false
    }

    static fromJSON(jsonData) {
        return jsonData.map((i) => i instanceof IndexDesc ? i : new IndexDesc(i))
    }
}


/**
 * Get the current request token for API and form requests.
 *
 * @returns {ApiToken} token
 */
export async function getApiToken() {
    return (await refreshGlobalState()).apiToken
}


/**
 * Get list of available indices from initial state.
 *
 * @returns {ApiToken} token
 */
export async function getAvailableIndices() {
    return (await refreshGlobalState()).indices
}

export class SearchResponse {
    constructor(meta, results) {
        this.meta = meta || {}
        this.results = results || []
    }
}

export class SearchModel {
    constructor({query = '', indices = [], page = 1, pageSize = 10, init = false} = {}) {
        this.query = query
        this.pageSize =  parseInt(pageSize)
        this.page = Math.max(1, parseInt(page))
        this.indices = indices
        this.response = null
        if (init) {
            this.initState()
        }
    }

    async initState() {
        this.indices = (await refreshGlobalState()).indices
    }

    async search(requestOptions) {
        ++GLOBAL_STATE.counter
        const response = await xhr(Object.assign({
            method: 'POST',
            url: import.meta.env.VITE_API_BACKEND_ADDRESS +'_search',
            withCredentials: true,
            headers: {
                'Authorization': 'Bearer ' + (await getApiToken()).token
            },
            data: this.toApiRequestBody(),
            timeout: 30000,
        }, requestOptions))
        return response.data
    }

    /**
     * Generate a query string object representation of the search model's request data.
     */
    toQueryStringObj() {
        let indices = this.selectedIndices().map((e) => e.id)
        return {
            q: this.query,
            index: indices.length === 1 ? indices[0] : indices,
            p: this.page,
        }
    }

    /**
     * Generate an API request body representation of the search model's request data.
     * @param additionalFields additional fields to add to the request body
     */
    toApiRequestBody(additionalFields = null) {
        if (!additionalFields) {
            additionalFields = {}
        }
        return objCamelToSnake({
            query: this.query,
            index: this.selectedIndices().map((e) => e.id),
            from: Math.max(0, this.page - 1) * this.pageSize,
            size: this.pageSize,
            _extendedMeta: true,
            ... additionalFields
        })
    }

    /**
     * Update model from search result JSON response.
     *
     * @param jsonData JSON response data
     */
    updateFromResponse(jsonData) {
        const response = new SearchResponse(objSnake2Camel(jsonData.meta), objSnake2Camel(jsonData.results))
        response.meta.indices = response.meta.indices.map((i) => new IndexDesc(i))
        this.response = response
        
        this.page = Math.floor(this.response.meta.resultsFrom / this.response.meta.pageSize) + 1
        this.pageSize = this.response.meta.pageSize
        this.indices = IndexDesc.fromJSON(this.response.meta.indices)
    }

    /**
     * Update request model data from a query string object and reset response.
     *
     * @param queryString query string Object
     */
    updateFromQueryString(queryString) {
        let queryIndices = queryString.index || []
        if (typeof queryIndices === 'string') {
            queryIndices = [queryIndices]
        }

        this.query = queryString.q || ''
        this.indices = this.indices.map((i) => Object.assign(
            {}, i, {selected: !queryIndices.length ? i.selected : queryIndices.includes(i.id)}))
        this.page = Math.max(1, parseInt(queryString.p) || 1)
        this.response = null
    }

    /**
     * Get maximum page from search result or 0 if unavailable.
     */
    maxPage() {
        if (!this.response) {
            return 0
        }
        return this.response.meta.maxPage
    }

    /**
     * Return the list of selected indices (i.e., `index.selected === true`).
     */
    selectedIndices() {
        return this.indices.filter((e) => e.selected)
    }
}
