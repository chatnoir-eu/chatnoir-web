/**
 * Build a query string from a parameter map.
 *
 * @param params parameters as map
 * @returns {string} query string
 */
export function buildQueryString(params) {
    return Object.keys(params).reduce((pList, k) => {
        if (Array.isArray(params[k])) {
            params[k].forEach((i) => pList.push(encodeURIComponent(k) + '=' + encodeURIComponent(i)))
        } else {
            pList.push(encodeURIComponent(k) + '=' + encodeURIComponent(params[k]))
        }
        return pList
    }, []).join('&')
}

/**
 * Return a query URL for the given route.
 *
 * @param route route for which to generate a query URL
 * @param query search query to add to query URL
 * @param index search index (use existing from route if unset)
 * @returns {string} query URL
 */
export function getQueryUrl(route, query, index = null) {
    const qs = Object.assign({}, route.query)
    qs.q = query
    if (index) {
        qs.index = index
    }
    return route.path + '?' + buildQueryString(qs)
}

/**
 * Escape HTML entities in a text.
 *
 * @param text input text
 * @returns {string}
 */
export function escapeHTML(text) {
    let e = document.createElement('_');
    e.innerText = text;
    return e.innerHTML;
}

/**
 * Abbreviate URL to at most ``maxSegments`` path segments.
 * Must be an absolute URL. Query string and fragment identifiers will be purged.
 *
 * @param url URL string to abbreviate
 * @param maxSegments: maximum number of segments
 * @param maxLength: maximum path length in characters (full URL may be longer)
 * @param replacement: abbreviation replacement character
 */
export function abbreviateUrl(url, maxSegments = 3, maxLength = 40,
                              replacement = '\u2009\u2026\u2009') {
    url = new URL(url)
    url.search = ''
    url.hash = ''

    let segments = url.pathname.substr(1).split(/\//)
    if (segments.length <= maxSegments && url.pathname.length <= maxLength) {
        return url.href
    }
    segments = segments.slice(-maxSegments)
    let path = segments.join('/').substr(-maxLength)
    return [url.origin, replacement, path].join('/')
}

/**
 * Convert rem units to px.
 *
 * @param rem rem units as float
 * @returns {number} px value
 */
export function rem2Px(rem) {
    return rem * parseFloat(getComputedStyle(document.documentElement).fontSize)
}
