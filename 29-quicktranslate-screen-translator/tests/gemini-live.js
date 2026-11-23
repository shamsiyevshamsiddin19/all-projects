#!/usr/bin/gjs -m
// Optional live smoke test. It reads the private local config and never prints it.
import GLib from 'gi://GLib';
import Gio from 'gi://Gio';
import Soup from 'gi://Soup';

const configPath = GLib.build_filenamev([GLib.get_user_config_dir(), 'quick-translate', 'providers.json']);
const [ok, bytes] = Gio.File.new_for_path(configPath).load_contents(null);
if (!ok) throw new Error('Private Gemini configuration is missing.');
const {apiKey} = JSON.parse(new TextDecoder().decode(bytes));
if (!apiKey) throw new Error('Private Gemini key is missing.');

const message = Soup.Message.new('POST', 'https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent');
message.request_headers.replace('x-goog-api-key', apiKey);
message.set_request_body_from_bytes('application/json', new GLib.Bytes(JSON.stringify({
    contents: [{parts: [{text: 'Return exactly {"ok":true} as JSON.'}]}],
    generationConfig: {responseMimeType: 'application/json', maxOutputTokens: 32},
})));
const session = new Soup.Session({timeout: 10});
const loop = new GLib.MainLoop(null, false);
let failed = null;
session.send_and_read_async(message, GLib.PRIORITY_DEFAULT, null, (client, result) => {
    try {
        const response = client.send_and_read_finish(result);
        if (message.status_code !== 200) {
            const errorBody = new TextDecoder().decode(response.get_data());
            const detail = JSON.parse(errorBody)?.error?.message || 'No diagnostic returned.';
            throw new Error(`Gemini HTTP ${message.status_code}: ${detail}`);
        }
        const body = JSON.parse(new TextDecoder().decode(response.get_data()));
        const text = body?.candidates?.[0]?.content?.parts?.find(part => typeof part?.text === 'string')?.text;
        if (JSON.parse(text).ok !== true) throw new Error('Unexpected Gemini response.');
    } catch (error) {
        failed = error;
    }
    loop.quit();
});
loop.run();
if (failed) throw failed;
print('Gemini live smoke test passed.');
