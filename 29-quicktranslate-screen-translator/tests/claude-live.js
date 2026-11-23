#!/usr/bin/gjs -m
// Optional live smoke test. It reads the private local config and never prints it.
import GLib from 'gi://GLib';
import Gio from 'gi://Gio';
import Soup from 'gi://Soup';
import {buildTranslationPrompt, parseClaudeTranslation} from '../gemini-utils.js';

const configPath = GLib.build_filenamev([GLib.get_user_config_dir(), 'quick-translate', 'providers.json']);
const [ok, bytes] = Gio.File.new_for_path(configPath).load_contents(null);
if (!ok) throw new Error('Private translation configuration is missing.');
const {claudeApiKey} = JSON.parse(new TextDecoder().decode(bytes));
if (!claudeApiKey) throw new Error('Private Claude key is missing.');

const message = Soup.Message.new('POST', 'https://api.anthropic.com/v1/messages');
message.request_headers.replace('x-api-key', claudeApiKey);
message.request_headers.replace('anthropic-version', '2023-06-01');
message.set_request_body_from_bytes('application/json', new GLib.Bytes(JSON.stringify({
    model: 'claude-sonnet-5-5',
    max_tokens: 256,
    system: 'You are a precise translation engine. Return only the required JSON object, never Markdown or an explanation.',
    messages: [{role: 'user', content: buildTranslationPrompt('Мой', 'auto')}],
})));
const session = new Soup.Session({timeout: 12});
const loop = new GLib.MainLoop(null, false);
let failed = null;
session.send_and_read_async(message, GLib.PRIORITY_DEFAULT, null, (client, result) => {
    try {
        const response = client.send_and_read_finish(result);
        if (message.status_code !== 200) {
            const errorBody = JSON.parse(new TextDecoder().decode(response.get_data()));
            throw new Error(`Claude HTTP ${message.status_code}: ${errorBody?.error?.message || 'No diagnostic returned.'}`);
        }
        const body = JSON.parse(new TextDecoder().decode(response.get_data()));
        const text = body?.content?.find(part => part?.type === 'text')?.text;
        const translation = parseClaudeTranslation(text, 'auto');
        if (translation.src !== 'RU' || translation.items[0]?.tag !== 'UZ' || translation.items[1]?.tag !== 'EN')
            throw new Error('Unexpected Claude translation response.');
    } catch (error) {
        failed = error;
    }
    loop.quit();
});
loop.run();
if (failed) throw failed;
print('Claude live smoke test passed.');
