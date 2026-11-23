/* Pure helpers for Gemini's structured quick-translation response. */

export function targetsFor(source) {
    return source === 'UZ' ? ['RU', 'EN'] :
        source === 'EN' ? ['UZ', 'RU'] : ['UZ', 'EN'];
}

export function extractFirstJsonObject(text) {
    if (typeof text !== 'string') return '';
    let start = -1;
    let depth = 0;
    let quoted = false;
    let escaped = false;
    for (let index = 0; index < text.length; index++) {
        const char = text[index];
        if (start < 0) {
            if (char === '{') {
                start = index;
                depth = 1;
            }
            continue;
        }
        if (escaped) {
            escaped = false;
            continue;
        }
        if (char === '\\' && quoted) {
            escaped = true;
            continue;
        }
        if (char === '"') {
            quoted = !quoted;
            continue;
        }
        if (quoted) continue;
        if (char === '{') depth++;
        if (char === '}' && --depth === 0) return text.slice(start, index + 1);
    }
    return '';
}

export function buildTranslationPrompt(text, requestedSource = 'auto') {
    const hint = requestedSource === 'auto' ?
        'Detect the source language yourself.' :
        `Treat the source language as ${requestedSource.toUpperCase()}.`;
    return `Translate the selected text faithfully. ${hint}\n` +
        'Supported source languages are Uzbek (UZ), Russian (RU), and English (EN). ' +
        'If UZ, return RU and EN. If EN, return UZ and RU. If RU, return UZ and EN. ' +
        'Keep names, numbers, punctuation, and line breaks when meaningful. ' +
        'Return only this exact JSON shape: {"src":"UZ|RU|EN","items":[{"tag":"TARGET","text":"translation"},{"tag":"TARGET","text":"translation"}]}. ' +
        'Use exactly the keys src, items, tag, and text; do not use source_language or language names as keys.\n\n' +
        `Selected text:\n${text}`;
}

export function parseGeminiTranslation(candidateText, requestedSource = 'auto') {
    if (typeof candidateText !== 'string' || !candidateText.trim())
        throw new Error('AI bo‘sh javob qaytardi.');

    let payload;
    try {
        payload = JSON.parse(candidateText);
    } catch (_error) {
        throw new Error('AI JSON javobi noto‘g‘ri.');
    }

    let source = typeof payload.src === 'string' ? payload.src.trim().toUpperCase() : '';
    if (requestedSource !== 'auto') source = requestedSource.toUpperCase();
    if (!['UZ', 'RU', 'EN'].includes(source))
        throw new Error('AI manba tilini aniqlay olmadi.');

    if (!Array.isArray(payload.items))
        throw new Error('AI tarjimalari topilmadi.');

    const wanted = targetsFor(source);
    const byTag = new Map();
    for (const item of payload.items) {
        const tag = typeof item?.tag === 'string' ? item.tag.trim().toUpperCase() : '';
        const value = typeof item?.text === 'string' ? item.text.trim() : '';
        if (wanted.includes(tag) && value && !byTag.has(tag)) byTag.set(tag, value);
    }

    if (!wanted.every(tag => byTag.has(tag)))
        throw new Error('AI to‘liq ikki tarjima qaytarmadi.');

    return {
        src: source,
        items: wanted.map(tag => ({tag, text: byTag.get(tag), error: null})),
    };
}

export function parseClaudeTranslation(candidateText, requestedSource = 'auto') {
    try {
        return parseGeminiTranslation(candidateText, requestedSource);
    } catch (initialError) {
        let raw;
        try {
            raw = JSON.parse(extractFirstJsonObject(candidateText));
        } catch (_error) {
            throw initialError;
        }
        const source = raw?.src || raw?.source_language;
        if (!source || !['UZ', 'RU', 'EN'].includes(String(source).toUpperCase()))
            throw initialError;
        const normalized = {
            src: String(source).toUpperCase(),
            items: Array.isArray(raw.items) ? raw.items :
                targetsFor(String(source).toUpperCase()).map(tag => ({tag, text: raw[tag]})),
        };
        return parseGeminiTranslation(JSON.stringify(normalized), requestedSource);
    }
}
