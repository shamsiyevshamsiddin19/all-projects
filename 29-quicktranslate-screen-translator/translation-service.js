import GLib from 'gi://GLib';
import Gio from 'gi://Gio';
import Soup from 'gi://Soup';
import {chooseExample} from './example-utils.js';
import {buildTranslationPrompt, parseClaudeTranslation, parseGeminiTranslation} from './gemini-utils.js';
import {TranslationOrchestrator} from './translation-orchestrator.js';

const soupSession = new Soup.Session({timeout: 12});
// Gemini gets a short, bounded attempt so the established Google path still
// completes inside the popup's 20 second overall deadline when needed.
const geminiSession = new Soup.Session({timeout: 6});
const claudeSession = new Soup.Session({timeout: 8});
const GEMINI_MODEL = 'gemini-3.8-flash';
const GEMINI_ENDPOINT = `https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent`;
const CLAUDE_MODEL = 'claude-sonnet-5-5';
const CLAUDE_ENDPOINT = 'https://api.anthropic.com/v1/messages';
const CLAUDE_API_VERSION = '2023-06-01';
const PROVIDER_CONFIG_PATH = GLib.build_filenamev([GLib.get_user_config_dir(), 'quick-translate', 'providers.json']);
const LEGACY_CONFIG_PATH = GLib.build_filenamev([GLib.get_user_config_dir(), 'quick-translate', 'gemini.json']);

function loadPrivateTranslationConfig() {
    // Keys are deliberately outside the extension and repository. Never log them.
    for (const path of [PROVIDER_CONFIG_PATH, LEGACY_CONFIG_PATH]) {
        try {
            const file = Gio.File.new_for_path(path);
            const [ok, bytes] = file.load_contents(null);
            if (ok) return JSON.parse(new TextDecoder().decode(bytes));
        } catch (_error) {
            // Try the backward-compatible path before treating config as absent.
        }
    }
    return {};
}

function loadGeminiApiKey() {
    const apiKey = loadPrivateTranslationConfig().apiKey;
    return typeof apiKey === 'string' ? apiKey.trim() : '';
}

function loadClaudeApiKey() {
    const apiKey = loadPrivateTranslationConfig().claudeApiKey;
    return typeof apiKey === 'string' ? apiKey.trim() : '';
}

export function fetchOne(text, src, tgt, callback, cancellable) {
    // Har bir so'rov bekor qilinadi; HTTP va javob tuzilishi tekshiriladi.
    const url = 'https://translate.googleapis.com/translate_a/single?client=dict-chrome-ex&sl=' +
        encodeURIComponent(src) + '&tl=' + encodeURIComponent(tgt) + '&dt=t&q=' + encodeURIComponent(text);
    const msg = Soup.Message.new('GET', url);
    soupSession.send_and_read_async(msg, GLib.PRIORITY_DEFAULT, cancellable, (session, res) => {
        let translated, detected, error;
        try {
            const bytes = session.send_and_read_finish(res);
            if (msg.status_code !== 200) throw new Error('Tarjima xizmati javob bermadi (' + msg.status_code + ').');
            const data = JSON.parse(new TextDecoder().decode(bytes.get_data()));
            if (!Array.isArray(data[0])) throw new Error('Tarjima javobi noto‘g‘ri.');
            translated = data[0].filter(Array.isArray).map(part => part[0] || '').join('');
            detected = typeof data[2] === 'string' ? data[2].toUpperCase() : src.toUpperCase();
            if (!translated) throw new Error('Tarjima topilmadi.');
        } catch (e) {
            error = 'Tarjima olinmadi. Internet aloqasini tekshirib, qayta urinib ko‘ring.';
        }
        if (!cancellable?.is_cancelled()) callback(translated, detected, error);
    });
}

function requestGoogleMultiTranslation(text, callback, cancellable, source = 'auto') {
    fetchOne(text, source, 'uz', (first, src, error) => {
        if (error) { callback(null, error); return; }
        if (source !== 'auto') src = source.toUpperCase();
        const targets = src === 'UZ' ? ['RU', 'EN'] : src === 'EN' ? ['UZ', 'RU'] : ['UZ', 'EN'];
        const items = new Array(2);
        let remaining = 2;
        const complete = (index, translation, failure) => {
            // Xatoda asl matnni boshqa til tarjimasi deb ko'rsatmaymiz.
            items[index] = {tag: targets[index], text: translation || '', error: failure || null};
            if (--remaining === 0) callback({src, items});
        };
        targets.forEach((target, index) => {
            if (target === 'UZ') complete(index, first, null);
            else fetchOne(text, src.toLowerCase(), target.toLowerCase(),
                (value, _source, failure) => complete(index, value, failure), cancellable);
        });
    }, cancellable);
}

function requestGeminiMultiTranslation(text, callback, cancellable, source = 'auto') {
    const apiKey = loadGeminiApiKey();
    if (!apiKey) {
        callback(null, 'Gemini kaliti sozlanmagan.');
        return;
    }

    const requestBody = JSON.stringify({
        contents: [{role: 'user', parts: [{text: buildTranslationPrompt(text, source)}]}],
        generationConfig: {
            temperature: 0,
            maxOutputTokens: 1024,
            responseMimeType: 'application/json',
            responseSchema: {
                type: 'OBJECT',
                properties: {
                    src: {type: 'STRING'},
                    items: {
                        type: 'ARRAY',
                        items: {
                            type: 'OBJECT',
                            properties: {tag: {type: 'STRING'}, text: {type: 'STRING'}},
                            required: ['tag', 'text'],
                        },
                    },
                },
                required: ['src', 'items'],
            },
        },
    });
    const message = Soup.Message.new('POST', GEMINI_ENDPOINT);
    message.request_headers.replace('x-goog-api-key', apiKey);
    message.set_request_body_from_bytes('application/json', new GLib.Bytes(requestBody));

    geminiSession.send_and_read_async(message, GLib.PRIORITY_DEFAULT, cancellable, (session, response) => {
        let result = null;
        let error = null;
        try {
            const bytes = session.send_and_read_finish(response);
            if (message.status_code !== 200)
                throw new Error(`Gemini HTTP ${message.status_code}`);
            const body = JSON.parse(new TextDecoder().decode(bytes.get_data()));
            const parts = body?.candidates?.[0]?.content?.parts;
            const candidateText = Array.isArray(parts) ? parts.find(part => typeof part?.text === 'string')?.text : '';
            result = parseGeminiTranslation(candidateText, source);
        } catch (failure) {
            // This error intentionally stays internal; Google is the automatic fallback.
            const code = message.status_code ? `HTTP_${message.status_code}` : 'NETWORK_OR_PARSE';
            console.warn(`[QuickTranslate] Gemini failed: ${code}`);
            error = code;
        }
        if (!cancellable?.is_cancelled()) callback(result, error);
    });
}

function requestClaudeMultiTranslation(text, callback, cancellable, source = 'auto') {
    const apiKey = loadClaudeApiKey();
    if (!apiKey) {
        callback(null, 'Claude kaliti sozlanmagan.');
        return;
    }
    const requestBody = JSON.stringify({
        model: CLAUDE_MODEL,
        max_tokens: 1024,
        system: 'You are a precise translation engine. Return only the required JSON object, never Markdown or an explanation.',
        messages: [{role: 'user', content: buildTranslationPrompt(text, source)}],
    });
    const message = Soup.Message.new('POST', CLAUDE_ENDPOINT);
    message.request_headers.replace('x-api-key', apiKey);
    message.request_headers.replace('anthropic-version', CLAUDE_API_VERSION);
    message.set_request_body_from_bytes('application/json', new GLib.Bytes(requestBody));

    claudeSession.send_and_read_async(message, GLib.PRIORITY_DEFAULT, cancellable, (session, response) => {
        let result = null;
        let error = null;
        try {
            const bytes = session.send_and_read_finish(response);
            if (message.status_code !== 200)
                throw new Error(`Claude HTTP ${message.status_code}`);
            const body = JSON.parse(new TextDecoder().decode(bytes.get_data()));
            const candidateText = Array.isArray(body?.content) ?
                body.content.find(part => part?.type === 'text' && typeof part.text === 'string')?.text : '';
            result = parseClaudeTranslation(candidateText, source);
        } catch (failure) {
            const code = message.status_code ? `HTTP_${message.status_code}` : 'NETWORK_OR_PARSE';
            console.warn(`[QuickTranslate] Claude failed: ${code}`);
            error = code;
        }
        if (!cancellable?.is_cancelled()) callback(result, error);
    });
}

export function requestMultiTranslation(text, callback, cancellable, source = 'auto') {
    // Claude is preferred when the user has configured it. We deliberately do
    // not issue Gemini and Claude requests together: both are paid APIs.
    const primary = loadClaudeApiKey() ? requestClaudeMultiTranslation : requestGeminiMultiTranslation;
    const coordinator = new TranslationOrchestrator(callback, () => cancellable?.is_cancelled() ?? false);
    coordinator.start(
        done => primary(text, done, cancellable, source),
        done => requestGoogleMultiTranslation(text, done, cancellable, source)
    );
}

export function fetchDictionaryExample(text, language, callback, cancellable) {
    const url = 'https://translate.googleapis.com/translate_a/single?client=dict-chrome-ex&dj=1&dt=ex&dt=md&sl=' +
        encodeURIComponent(language.toLowerCase()) + '&tl=' + (language === 'EN' ? 'uz' : 'en') +
        '&q=' + encodeURIComponent(text);
    const message = Soup.Message.new('GET', url);
    soupSession.send_and_read_async(message, GLib.PRIORITY_DEFAULT, cancellable, (session, response) => {
        let example = '', failed = false;
        try {
            const bytes = session.send_and_read_finish(response);
            if (message.status_code !== 200) throw new Error('HTTP error');
            const data = JSON.parse(new TextDecoder().decode(bytes.get_data()));
            example = chooseExample(data);
        } catch (_error) { failed = true; }
        if (!cancellable.is_cancelled()) callback(example, failed);
    });
}
