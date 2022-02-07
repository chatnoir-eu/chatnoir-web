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


import { objSnake2Camel } from '@/common'

/**
 * Index meta descriptor.
 */
export class IndexDesc {
    constructor({id, name, selected}) {
        this.id = id
        this.name = name
        this.selected = selected || false
    }
}

export class SearchResponse {
    constructor(meta, hits) {
        this.meta = meta || {}
        this.hits = hits || []
    }
}

export class SearchModel {
    constructor({query, indices, page, pageSize, maxPage} = {}) {
        this.query = query || ''
        this.indices = indices || []
        this.pageSize =  parseInt(pageSize) || 10
        this.maxPage =  parseInt(maxPage) || 1000
        this.page = Math.min(this.maxPage, Math.max(1, parseInt(page)) || 1)
        this.response = null
    }

    /**
     * Generate a query string Map object representation of this search model's request data.
     */
    toQueryString() {
        let indices = this.indices ? this.indices.filter((e) => e.selected).map((e) => e.id) : []
        const m = {
            q: this.query,
            index: indices.length === 1 ? indices[0] : indices
        }
        if (this.page > 1) {
            m.p = this.page
        }

        return m
    }

    /**
     * Update model from search result JSON response.
     *
     * @param jsonData JSON response data
     */
    updateFromResponse(jsonData) {
        this.response = new SearchResponse(objSnake2Camel(jsonData.meta), objSnake2Camel(jsonData.hits))
        this.response.meta.indicesAll = this.response.meta.indicesAll.map((i) => new IndexDesc(i))
        this.indices = this.response.meta.indicesAll
        this.page = this.response.meta.page
        this.maxPage = this.response.meta.maxPage
        this.pageSize = this.response.meta.pageSize
    }

    /**
     * Update request model data from a query string object and reset response.
     *
     * @param queryString query string Object
     * @param availableIndices {IndexDesc[]} list of available indices as IndexDesc objects
     */
    updateFromQueryString(queryString, availableIndices) {
        let indices = queryString.index || []
        if (typeof indices === 'string') {
            indices = [indices]
        }

        this.query = queryString.q || ''
        this.indices = availableIndices.map((i) => Object.assign(
            {}, i, {selected: !indices.length ? i.selected : indices.includes(i.id)}))
        this.page = Math.min(this.pageMax, Math.max(1, parseInt(queryString.p) || 1))
        this.response = null
    }
}
