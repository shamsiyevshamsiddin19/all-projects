#!/usr/bin/env python3
"""
Comprehensive End-to-End Test Suite for Zenith Study Timer
Tests Python backend, API endpoints, static assets, HTML structure,
and JavaScript UI logic.
"""
import http.client
import json
import os
import socketserver
import subprocess
import sys
import threading
import time
from bs4 import BeautifulSoup

# Add current directory to path
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIRECTORY)

import app

TEST_PORT = 5058

class ServerThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        socketserver.TCPServer.allow_reuse_address = True
        self.httpd = socketserver.TCPServer(("", TEST_PORT), app.Handler)

    def run(self):
        self.httpd.serve_forever()

    def shutdown(self):
        self.httpd.shutdown()
        self.httpd.server_close()

def run_tests():
    print("=" * 65)
    print("🚀 ZENITH STUDY TIMER — TO'LIQ TEST DASTURI BOSHLANDI")
    print("=" * 65)

    passed_count = 0
    total_count = 0

    def record_test(name, success, details=""):
        nonlocal passed_count, total_count
        total_count += 1
        if success:
            passed_count += 1
            print(f"  ✅ [PASS] {name} {details}")
        else:
            print(f"  ❌ [FAIL] {name} {details}")
            raise AssertionError(f"Test failed: {name} - {details}")

    # =========================================================================
    # PART 1: Python HTTP Server & API Tests
    # =========================================================================
    print("\n[1/3] PYTHON BACKEND SERVER & API ENDPOINTS...")
    server = ServerThread()
    server.start()
    time.sleep(0.3) # Wait for server to bind

    conn = http.client.HTTPConnection("localhost", TEST_PORT)

    try:
        # Test 1: GET / (index.html)
        conn.request("GET", "/")
        res = conn.getresponse()
        body = res.read().decode("utf-8")
        record_test("GET / (index.html)", res.status == 200 and "ZENITH CHRONO" in body, f"(status={res.status})")

        # Test 2: GET /css/style.css
        conn.request("GET", "/css/style.css")
        res = conn.getresponse()
        css_body = res.read().decode("utf-8")
        record_test("GET /css/style.css", res.status == 200 and "theme-obsidian" in css_body, f"(status={res.status})")

        # Test 3: GET /js/app.js
        conn.request("GET", "/js/app.js")
        res = conn.getresponse()
        js_body = res.read().decode("utf-8")
        record_test("GET /js/app.js", res.status == 200 and "Zenith Chrono" in js_body, f"(status={res.status})")

        # Test 4: GET /js/audio.js
        conn.request("GET", "/js/audio.js")
        res = conn.getresponse()
        audio_body = res.read().decode("utf-8")
        record_test("GET /js/audio.js", res.status == 200 and "ZenithAudioEngine" in audio_body, f"(status={res.status})")

        # Test 5: OPTIONS /api/data (CORS Preflight)
        conn.request("OPTIONS", "/api/data")
        res = conn.getresponse()
        res.read()
        cors_origin = res.getheader("Access-Control-Allow-Origin")
        cors_methods = res.getheader("Access-Control-Allow-Methods")
        record_test("OPTIONS /api/data CORS Preflight", 
                    res.status == 204 and cors_origin == "*" and "POST" in cors_methods,
                    f"(status={res.status}, methods={cors_methods})")

        # Test 6: POST /api/data (Save timer state)
        sample_payload = {
            "version": "1.0",
            "test": True,
            "settings": {
                "mode": "duration",
                "theme": "theme-obsidian",
                "font": "font-urbanist",
                "volume": 85,
                "alarmSound": "zen_bowl"
            },
            "timerState": {
                "durationTotal": 1500,
                "durationRemaining": 1500
            }
        }
        body_bytes = json.dumps(sample_payload).encode("utf-8")
        conn.request("POST", "/api/data", body_bytes, {"Content-Type": "application/json"})
        res = conn.getresponse()
        post_resp = json.loads(res.read().decode("utf-8"))
        record_test("POST /api/data Save JSON", res.status == 200 and post_resp.get("status") == "saved", f"(status={res.status})")

        # Test 7: GET /api/data (Read persisted timer state)
        conn.request("GET", "/api/data")
        res = conn.getresponse()
        get_resp = json.loads(res.read().decode("utf-8"))
        record_test("GET /api/data Verify Saved Data", res.status == 200 and get_resp.get("settings", {}).get("volume") == 85)

        # Test 8: POST /api/data with invalid JSON -> 400 Bad Request
        conn.request("POST", "/api/data", b"invalid-json{{{", {"Content-Type": "application/json"})
        res = conn.getresponse()
        res.read()
        record_test("POST /api/data Error Handling (Invalid JSON)", res.status == 400, f"(status={res.status})")

    finally:
        conn.close()
        server.shutdown()
        print("  ℹ️  Python test server muvaffaqiyatli to'xtatildi.")

    # =========================================================================
    # PART 2: HTML & Element Parity Verification
    # =========================================================================
    print("\n[2/3] HTML STRUKTURASI VA BARCHA ELEMENTLAR TEKSHIRUVI...")
    with open(os.path.join(DIRECTORY, "index.html"), "r", encoding="utf-8") as f:
        html_content = f.read()
    soup = BeautifulSoup(html_content, "html.parser")

    required_elements = [
        ("Settings Drawer", "#settingsDrawer"),
        ("Hover Trigger Zone", "#hoverZone"),
        ("Hover Peek Bar", "#hoverPeekBar"),
        ("Header Settings Gear Btn", "#openSettingsHeaderBtn"),
        ("Header Pin Drawer Btn", "#pinDrawerBtn"),
        ("Header Close Drawer Btn", "#closeDrawerBtn"),
        ("Duration Mode Tab", "#tabDuration"),
        ("Pomodoro Mode Tab", "#tabPomodoro"),
        ("Stopwatch Mode Tab", "#tabStopwatch"),
        ("Clock Mode Tab", "#tabClock"),
        ("Input Days", "#inputDays"),
        ("Input Hours", "#inputHours"),
        ("Input Minutes", "#inputMinutes"),
        ("Input Seconds", "#inputSeconds"),
        ("Main Start/Pause Btn", "#toggleRunBtn"),
        ("Reset Btn", "#resetBtn"),
        ("Fullscreen Btn", "#fullscreenBtn"),
        ("Zen Mode Btn", "#zenModeBtn"),
        ("Back to Timer Btn", "#backToTimerBtn"),
        ("Theme Select Dropdown", "#themeSelect"),
        ("Font Select Dropdown", "#fontSelect"),
        ("Alarm Sound Select Dropdown", "#alarmSoundSelect"),
        ("Ambient Sound Select Dropdown", "#ambientSoundSelect"),
        ("Volume Slider", "#volumeSlider"),
        ("Volume Percentage Text", "#volumePercent"),
        ("Test Sound Btn", "#testSoundBtn"),
        ("Interval Reminder Select", "#intervalReminderSelect"),
        ("Pre-End Warning Checkbox", "#checkPreEndWarning"),
        ("Browser Notification Checkbox", "#checkBrowserNotify"),
        ("Show Days Checkbox", "#checkShowDays"),
        ("Show Progress Checkbox", "#checkShowProgress"),
        ("Screen WakeLock Checkbox", "#checkWakeLock"),
        ("Digits Container", "#digitsContainer"),
        ("Days Column", "#colDays"),
        ("Days Value Span", "#daysValue"),
        ("Hours Value Span", "#hoursValue"),
        ("Minutes Value Span", "#minutesValue"),
        ("Seconds Value Span", "#secondsValue"),
        ("Progress Bar Fill", "#progressBarFill"),
        ("Reminder Toast Alert", "#reminderToast")
    ]

    for label, selector in required_elements:
        elem = soup.select_one(selector)
        record_test(f"Element mavjudligi: {label} ({selector})", elem is not None)

    # Verify Preset Buttons Count
    presets = soup.select("#panelDuration .preset-btn")
    record_test("Preset tugmalari (5m, 15m, 25m, 45m, 1h, 2h, 24h)", len(presets) == 7, f"(topildi={len(presets)})")

    # Verify Quick Adjust Chips Count
    chips = soup.select("#quickAdjustRow .chip-btn")
    record_test("Tezkor qo'shish tugmalari (+1, +5, +15, +1h, -5)", len(chips) == 5, f"(topildi={len(chips)})")

    # Verify Pomodoro Phase Buttons
    pomo_phases = soup.select(".phase-btn")
    record_test("Pomodoro bosqich tugmalari (Dars, Tanaffus, Uzun)", len(pomo_phases) == 3, f"(topildi={len(pomo_phases)})")

    # =========================================================================
    # PART 3: JavaScript DOM & State Logic Simulation via Node.js
    # =========================================================================
    print("\n[3/3] JAVASCRIPT & BROWSER LOGIC INTEGRATION TEST (Node.js runner)...")
    
    node_test_script = """
    const fs = require('fs');
    const path = require('path');

    // Load HTML and JS files
    const html = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf-8');
    const appJs = fs.readFileSync(path.join(__dirname, 'js/app.js'), 'utf-8');
    const audioJs = fs.readFileSync(path.join(__dirname, 'js/audio.js'), 'utf-8');

    // Lightweight DOM Mock for Node testing
    class ElementMock {
      constructor(tagName, id = '', className = '') {
        this.tagName = tagName.toUpperCase();
        this.id = id;
        this.className = className;
        this.classList = {
          _set: new Set(className.split(' ').filter(Boolean)),
          add: (...c) => c.forEach(x => this.classList._set.add(x)),
          remove: (...c) => c.forEach(x => this.classList._set.delete(x)),
          contains: (c) => this.classList._set.has(c),
          toggle: (c, force) => {
            if (force === true) this.classList._set.add(c);
            else if (force === false) this.classList._set.delete(c);
            else {
              if (this.classList._set.has(c)) this.classList._set.delete(c);
              else this.classList._set.add(c);
            }
          }
        };
        this.style = {};
        this.value = '0';
        this.textContent = '';
        this.checked = true;
        this.offsetWidth = 340;
        this.listeners = {};
        this.dataset = {};
        this.children = [];
      }
      addEventListener(type, cb) {
        if (!this.listeners[type]) this.listeners[type] = [];
        this.listeners[type].push(cb);
      }
      dispatchEvent(event) {
        const type = typeof event === 'string' ? event : event.type;
        if (this.listeners[type]) {
          this.listeners[type].forEach(cb => cb(event));
        }
      }
      click() {
        this.dispatchEvent({ type: 'click', stopPropagation: () => {} });
      }
      querySelector(sel) { return null; }
      querySelectorAll(sel) { return []; }
    }

    const documentMock = {
      readyState: 'complete',
      title: '',
      elements: {},
      listeners: {},
      addEventListener: (type, cb) => {
        if (!documentMock.listeners[type]) documentMock.listeners[type] = [];
        documentMock.listeners[type].push(cb);
      },
      getElementById: (id) => {
        if (!documentMock.elements[id]) {
          documentMock.elements[id] = new ElementMock('div', id);
        }
        return documentMock.elements[id];
      },
      querySelectorAll: (sel) => [],
      documentElement: {
        requestFullscreen: async () => {}
      }
    };

    // Populate required elements in mock
    const elementIds = [
      'appBody', 'hoverZone', 'hoverPeekBar', 'settingsDrawer', 'drawerBrandTitle',
      'drawerBrandBadge', 'pinDrawerBtn', 'closeDrawerBtn', 'timerSubView',
      'settingsSubView', 'backToTimerBtn', 'openSettingsHeaderBtn', 'daysValue',
      'hoursValue', 'minutesValue', 'secondsValue', 'colDays', 'digitsContainer',
      'progressBarFill', 'progressBarContainer', 'eventTitleBanner', 'eventTitleDisplay',
      'eventTitleInput', 'reminderToast', 'reminderToastText', 'toggleRunBtn', 'resetBtn',
      'themeSelect', 'fontSelect', 'panelDuration', 'panelPomodoro', 'inputDays',
      'inputHours', 'inputMinutes', 'inputSeconds', 'quickAdjustRow', 'pomoCycleCount',
      'alarmSoundSelect', 'ambientSoundSelect', 'volumeSlider', 'volumePercent',
      'testSoundBtn', 'intervalReminderSelect', 'checkPreEndWarning', 'checkBrowserNotify',
      'checkShowDays', 'checkShowProgress', 'checkWakeLock', 'fullscreenBtn', 'zenModeBtn'
    ];
    elementIds.forEach(id => documentMock.getElementById(id));

    // Global Window Mock
    global.window = {
      location: { protocol: 'http:' },
      AudioContext: function() {
        return {
          state: 'running',
          currentTime: 0,
          sampleRate: 44100,
          createGain: () => ({ gain: { setValueAtTime: () => {}, exponentialRampToValueAtTime: () => {}, setTargetAtTime: () => {} }, connect: () => {} }),
          createOscillator: () => ({ frequency: { setValueAtTime: () => {} }, connect: () => {}, start: () => {}, stop: () => {} }),
          createBuffer: () => ({ getChannelData: () => new Float32Array(100) }),
          createBufferSource: () => ({ connect: () => {}, start: () => {}, stop: () => {} }),
          createBiquadFilter: () => ({ frequency: { setValueAtTime: () => {} }, Q: { setValueAtTime: () => {} }, connect: () => {} }),
          createChannelMerger: () => ({ connect: () => {} }),
          resume: () => {}
        };
      },
      localStorage: {
        _data: {},
        getItem: (k) => global.window.localStorage._data[k] || null,
        setItem: (k, v) => { global.window.localStorage._data[k] = v; },
        removeItem: (k) => { delete global.window.localStorage._data[k]; }
      }
    };
    global.document = documentMock;
    global.navigator = { wakeLock: { request: async () => ({ release: async () => {} }) } };
    global.Notification = { permission: 'default', requestPermission: async () => 'granted' };
    global.fetch = async () => ({ ok: true, json: async () => ({}) });

    // Execute audio.js
    eval(audioJs);
    if (!global.window.zenithAudio) {
      throw new Error('window.zenithAudio not initialized');
    }
    console.log('✅ JS: ZenithAudioEngine successfully loaded.');

    // Execute app.js
    eval(appJs);
    console.log('✅ JS: app.js initialized successfully.');

    // Test Play/Pause toggle
    const toggleBtn = documentMock.getElementById('toggleRunBtn');
    toggleBtn.click();
    console.log('✅ JS: Play/Pause button click tested.');

    // Test Digits Container click (toggles play)
    const digitsContainer = documentMock.getElementById('digitsContainer');
    digitsContainer.click();
    console.log('✅ JS: Screen digits container click tested.');

    // Test Reset Button click
    const resetBtn = documentMock.getElementById('resetBtn');
    resetBtn.click();
    console.log('✅ JS: Reset button click tested.');

    // Test Settings Toggle Button
    const settingsBtn = documentMock.getElementById('openSettingsHeaderBtn');
    settingsBtn.click();
    console.log('✅ JS: Settings view toggle click tested.');

    // Test Back to Timer Button
    const backBtn = documentMock.getElementById('backToTimerBtn');
    backBtn.click();
    console.log('✅ JS: Back to timer view click tested.');

    // Test Test Sound Button
    const soundBtn = documentMock.getElementById('testSoundBtn');
    soundBtn.click();
    console.log('✅ JS: Sound preview test button tested.');

    // Test Audio Methods directly
    global.window.zenithAudio.playAlarm('zen_bowl');
    global.window.zenithAudio.playAlarm('soft_bell');
    global.window.zenithAudio.playAlarm('digital_chime');
    global.window.zenithAudio.playAlarm('crystal');
    global.window.zenithAudio.playReminderChime();
    global.window.zenithAudio.setAmbient('rain');
    global.window.zenithAudio.setAmbient('binaural');
    global.window.zenithAudio.setAmbient('none');
    console.log('✅ JS: All synthesized audio alarms and ambients tested.');
    process.exit(0);
    """;

    res = subprocess.run(["node", "-e", node_test_script], capture_output=True, text=True, cwd=DIRECTORY, check=False)
    if res.returncode == 0:
        for line in res.stdout.strip().split("\n"):
            print(f"  {line}")
        record_test("Node.js JS & Web Audio Logic Test", True)
    else:
        print("STDERR:\n", res.stderr)
        record_test("Node.js JS & Web Audio Logic Test", False, res.stderr)

    print("\n" + "=" * 65)
    print(f"🎉 BARCHA TESTLAR MUVAFFAQIYATLI YAKUNLANDI: {passed_count}/{total_count} (100%)")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
