
// merged from assets/js/shared/remote-storage.js

(function () {
    if (window.RemoteStorageBridge) {
        return;
    }

    var logger = window.AppLogger || {
        info: function () {},
        warn: function () {},
        error: function () {},
    };

    var canPatchStorage = location.protocol !== 'file:' && typeof window.Storage !== 'undefined';
    var nativeGetItem = canPatchStorage ? Storage.prototype.getItem : null;
    var nativeSetItem = canPatchStorage ? Storage.prototype.setItem : null;
    var nativeRemoveItem = canPatchStorage ? Storage.prototype.removeItem : null;
    var nativeClear = canPatchStorage ? Storage.prototype.clear : null;
    var nativeKey = canPatchStorage ? Storage.prototype.key : null;
    var nativeLengthDescriptor = canPatchStorage ? Object.getOwnPropertyDescriptor(Storage.prototype, 'length') : null;
    var pendingBackupKey = '__remote_storage_pending_ops_v1';
    var broadcastFallbackKey = '__remote_storage_broadcast_v1';

    var state = {
        ready: false,
        syncEnabled: canPatchStorage,
        cache: {},
        queue: {},
        flushTimer: null,
        bootstrapPromise: null,
        bootstrapTimeoutMs: 4500,
        endpoint: '/api',
        keepalivePayloadLimit: 55000,
        largeValueThreshold: 50000,
        syncRetryDelayMs: 600,
        maxSyncRetryDelayMs: 30000,
        tabId: 'tab-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2),
        sequence: 0,
        keyVersions: {},
        clearStamp: 0,
        channel: null,
    };

    function isLocalStorageTarget(storageRef) {
        return canPatchStorage && storageRef === window.localStorage;
    }

    function toStringValue(value) {
        if (value === null || value === undefined) {
            return '';
        }

        return String(value);
    }

    function cacheKeys() {
        return Object.keys(state.cache);
    }

    function isInternalKey(key) {
        return String(key || '').indexOf('__remote_storage_') === 0;
    }

    function listNativeKeys() {
        var keys = [];

        if (!canPatchStorage) {
            return keys;
        }

        try {
            for (var index = 0; index < window.localStorage.length; index += 1) {
                var key = nativeKey.call(window.localStorage, index);
                if (key !== null && !isInternalKey(key)) {
                    keys.push(key);
                }
            }
        } catch (error) {
            logger.warn('Native localStorage keys could not be read', {
                error: error.message,
            });
        }

        return keys;
    }

    function purgeNativeStorage() {
        if (!canPatchStorage) {
            return;
        }

        try {
            listNativeKeys().forEach(function (key) {
                nativeRemoveItem.call(window.localStorage, key);
            });
        } catch (error) {
            logger.warn('Native localStorage could not be cleared', {
                error: error.message,
            });
        }
    }

    function safeParsePendingOps() {
        if (!canPatchStorage) {
            return [];
        }

        try {
            var raw = nativeGetItem.call(window.localStorage, pendingBackupKey);
            var parsed = raw ? JSON.parse(raw) : [];
            return Array.isArray(parsed) ? parsed.filter(function (op) {
                return op && typeof op.key === 'string' && op.key !== '';
            }) : [];
        } catch (error) {
            logger.warn('Pending storage ops could not be read', {
                error: error.message,
            });
            return [];
        }
    }

    function writePendingOps(ops) {
        if (!canPatchStorage) {
            return;
        }

        try {
            if (!ops.length) {
                nativeRemoveItem.call(window.localStorage, pendingBackupKey);
                return;
            }

            nativeSetItem.call(window.localStorage, pendingBackupKey, JSON.stringify(ops));
        } catch (error) {
            logger.warn('Pending storage ops could not be saved locally', {
                count: ops.length,
                error: error.message,
            });
        }
    }

    function rememberPendingOp(op) {
        if (!op || !op.key || op.type !== 'set') {
            return;
        }

        var ops = safeParsePendingOps().filter(function (item) {
            return item.key !== op.key;
        });

        ops.push({
            key: op.key,
            type: op.type,
            value: String(op.value || ''),
            stamp: normalizeStamp(op.stamp) || makeStamp(),
        });
        writePendingOps(ops);
    }

    function forgetPendingOps(ops) {
        if (!ops || !ops.length) {
            return;
        }

        var pending = safeParsePendingOps();
        if (!pending.length) {
            return;
        }

        var next = pending.filter(function (pendingOp) {
            return !ops.some(function (op) {
                return op
                    && op.key === pendingOp.key
                    && op.type === pendingOp.type
                    && String(op.value || '') === String(pendingOp.value || '');
            });
        });

        if (next.length !== pending.length) {
            writePendingOps(next);
        }
    }

    function forgetPendingKey(key) {
        var pending = safeParsePendingOps();
        if (!pending.length) {
            return;
        }

        var next = pending.filter(function (pendingOp) {
            return pendingOp.key !== key;
        });

        if (next.length !== pending.length) {
            writePendingOps(next);
        }
    }

    function forgetPendingBeforeStamp(stamp) {
        var pending = safeParsePendingOps();
        if (!pending.length) {
            return;
        }

        var normalizedStamp = normalizeStamp(stamp);
        var next = pending.filter(function (pendingOp) {
            return normalizeStamp(pendingOp.stamp) > normalizedStamp;
        });

        if (next.length !== pending.length) {
            writePendingOps(next);
        }
    }

    function payloadLength(ops) {
        return JSON.stringify({ ops: ops || [] }).length;
    }

    function makeStamp() {
        state.sequence += 1;
        return Date.now() * 1000 + state.sequence;
    }

    function normalizeStamp(stamp) {
        var parsed = Number(stamp || 0);
        return Number.isFinite(parsed) ? parsed : 0;
    }

    function rememberKeyVersion(key, stamp) {
        state.keyVersions[key] = Math.max(state.keyVersions[key] || 0, normalizeStamp(stamp));
    }

    function canApplyIncoming(key, stamp) {
        return normalizeStamp(stamp) >= (state.keyVersions[key] || 0);
    }

    function pruneQueuedKey(key, stamp) {
        if (!state.queue[key]) {
            return;
        }

        if (normalizeStamp(state.queue[key].stamp) <= normalizeStamp(stamp)) {
            delete state.queue[key];
        }
    }

    function broadcastStorageMessage(message) {
        if (!message) {
            return;
        }

        var enriched = Object.assign({
            source: state.tabId,
            sentAt: Date.now(),
        }, message);

        try {
            if (state.channel) {
                state.channel.postMessage(enriched);
            }
        } catch (error) {
            logger.warn('Storage broadcast failed', {
                error: error.message,
            });
        }

        try {
            if (canPatchStorage) {
                var payload = JSON.stringify(Object.assign({
                    fallbackId: state.tabId + '-' + Date.now() + '-' + Math.random().toString(36).slice(2),
                }, enriched));
                if (payload.length < state.keepalivePayloadLimit) {
                    nativeSetItem.call(window.localStorage, broadcastFallbackKey, payload);
                    nativeRemoveItem.call(window.localStorage, broadcastFallbackKey);
                }
            }
        } catch (error) {
            logger.warn('Storage fallback broadcast failed', {
                error: error.message,
            });
        }
    }

    function broadcastStorageOp(op) {
        broadcastStorageMessage({
            kind: 'storage-op',
            op: op,
        });
    }

    function applyIncomingStorageMessage(message) {
        if (!message || message.source === state.tabId) {
            return;
        }

        if (message.kind === 'storage-clear') {
            var clearStamp = normalizeStamp(message.stamp);
            if (clearStamp < state.clearStamp) {
                return;
            }

            state.clearStamp = clearStamp;
            var clearedKeys = [];
            Object.keys(state.cache).forEach(function (key) {
                if ((state.keyVersions[key] || 0) <= clearStamp) {
                    delete state.cache[key];
                    clearedKeys.push(key);
                }
            });
            Object.keys(state.queue).forEach(function (key) {
                if (normalizeStamp(state.queue[key].stamp) <= clearStamp) {
                    delete state.queue[key];
                }
            });
            Object.keys(state.keyVersions).forEach(function (key) {
                if ((state.keyVersions[key] || 0) <= clearStamp) {
                    delete state.keyVersions[key];
                }
            });
            forgetPendingBeforeStamp(clearStamp);

            if (!state.syncEnabled && canPatchStorage) {
                clearedKeys.forEach(function (key) {
                    nativeRemoveItem.call(window.localStorage, key);
                });
            }
            return;
        }

        if (message.kind !== 'storage-op' || !message.op || !message.op.key) {
            return;
        }

        var op = message.op;
        var key = String(op.key);
        var stamp = normalizeStamp(op.stamp);

        if (!canApplyIncoming(key, stamp)) {
            return;
        }

        if (op.type === 'delete') {
            delete state.cache[key];
            rememberKeyVersion(key, stamp);
            pruneQueuedKey(key, stamp);
            forgetPendingKey(key);

            if (!state.syncEnabled && canPatchStorage) {
                nativeRemoveItem.call(window.localStorage, key);
            }
            return;
        }

        state.cache[key] = String(op.value || '');
        rememberKeyVersion(key, stamp);
        pruneQueuedKey(key, stamp);
        forgetPendingKey(key);

        if (!state.syncEnabled && canPatchStorage) {
            nativeSetItem.call(window.localStorage, key, state.cache[key]);
        }
    }

    function setupTabSync() {
        if (typeof BroadcastChannel !== 'undefined') {
            try {
                state.channel = new BroadcastChannel('yordamchi_remote_storage_v1');
                state.channel.onmessage = function (event) {
                    applyIncomingStorageMessage(event.data);
                };
            } catch (error) {
                state.channel = null;
                logger.warn('BroadcastChannel could not be opened', {
                    error: error.message,
                });
            }
        }

        window.addEventListener('storage', function (event) {
            if (event.key !== broadcastFallbackKey || !event.newValue) {
                return;
            }

            try {
                applyIncomingStorageMessage(JSON.parse(event.newValue));
            } catch (error) {
                logger.warn('Storage fallback message could not be parsed', {
                    error: error.message,
                });
            }
        });
    }

    function isKeepaliveSafe(ops) {
        return payloadLength(ops) < state.keepalivePayloadLimit;
    }

    function isLargeSetOp(op) {
        return op && op.type === 'set' && !isKeepaliveSafe([op]);
    }

    function restorePendingBackups() {
        var ops = safeParsePendingOps();
        if (!ops.length) {
            return;
        }

        ops.forEach(function (op) {
            var stamp = normalizeStamp(op.stamp) || makeStamp();
            if (op.type === 'delete') {
                delete state.cache[op.key];
            } else {
                state.cache[op.key] = String(op.value || '');
            }
            rememberKeyVersion(op.key, stamp);
            state.queue[op.key] = {
                type: op.type || 'set',
                value: op.type === 'delete' ? null : String(op.value || ''),
                stamp: stamp,
            };
        });

        logger.info('Pending large storage ops restored', {
            count: ops.length,
        });
        scheduleFlush(0);
    }

    function migrateLegacyLocalStorage() {
        var keys = listNativeKeys();
        var changed = false;

        keys.forEach(function (key) {
            if (!Object.prototype.hasOwnProperty.call(state.cache, key)) {
                state.cache[key] = nativeGetItem.call(window.localStorage, key);
                if (state.syncEnabled) {
                    var stamp = makeStamp();
                    rememberKeyVersion(key, stamp);
                    state.queue[key] = {
                        type: 'set',
                        value: state.cache[key],
                        stamp: stamp,
                    };
                }
                changed = true;
            }
        });

        if (keys.length && state.syncEnabled) {
            purgeNativeStorage();
            logger.info('Legacy browser storage was removed', {
                keys: keys.length,
            });
        }

        if (changed && state.syncEnabled) {
            scheduleFlush(50);
            logger.info('Legacy browser storage was moved to server queue', {
                keys: keys.length,
            });
        }
    }

    /* ---------- MAHALLIY SURAT (ilova DARHOL ochilishi uchun) ----------
       Bu ko'prik localStorage'ni butunlay o'z ustiga oladi: o'qishlar
       `state.cache` dan keladi, u esa `storage_bootstrap` javobi bilan
       to'ladi. Shu sababli ilova javob KELMAGUNCHA hech narsa ko'rsata
       olmasdi — splash ekran turaverardi (bootstrap.js da 4 soniyagacha
       kutish chegarasi bor edi). Ochilishdagi "kutish" aynan shundan.

       Yechim: oxirgi ma'lum holat qurilmaning O'ZIDA surat sifatida
       saqlanadi. Keyingi ochilishda u SINXRON o'qiladi va ilova darhol
       chiziladi; server javobi orqa fonda keladi va farq bo'lsagina
       `remote-storage:refreshed` hodisasi bilan qayta chizdiradi.

       Surat kaliti `__remote_storage_` bilan boshlanadi, ya'ni
       `isInternalKey()` uni ichki deb biladi: `listNativeKeys()` ko'rmaydi,
       demak sinxronizatsiyaga ham, `purgeNativeStorage()` ga ham tushmaydi. */
    var snapshotKey = '__remote_storage_snapshot_v1';
    var snapshotTimer = null;

    function readSnapshot() {
        if (!canPatchStorage) {
            return null;
        }

        try {
            var raw = nativeGetItem.call(window.localStorage, snapshotKey);
            if (!raw) {
                return null;
            }

            var parsed = JSON.parse(raw);
            return parsed && typeof parsed.items === 'object' ? parsed.items : null;
        } catch (error) {
            return null;
        }
    }

    function writeSnapshot() {
        if (!canPatchStorage || !state.syncEnabled) {
            return;
        }

        try {
            nativeSetItem.call(
                window.localStorage,
                snapshotKey,
                JSON.stringify({ at: Date.now(), items: state.cache || {} })
            );
        } catch (error) {
            /* Kvota to'lsa surat saqlanmaydi — ilova baribir ishlayveradi,
               faqat keyingi ochilish yana serverni kutadi. */
            logger.warn('Storage snapshot could not be saved', {
                error: error.message,
            });
        }
    }

    function scheduleSnapshot() {
        clearTimeout(snapshotTimer);
        snapshotTimer = setTimeout(writeSnapshot, 400);
    }

    /* Server holatini surat ustiga qo'yadi. Hali yuborilmagan mahalliy
       o'zgarishlar (`state.queue`) YO'QOLMAYDI — ular server qiymatining
       ustidan yoziladi, aks holda foydalanuvchi endigina yozgan narsa
       orqa fondagi javob kelishi bilan yo'q bo'lardi. */
    function applyServerItems(items) {
        var next = Object.assign({}, items || {});

        Object.keys(state.queue).forEach(function (key) {
            if (state.queue[key].type === 'delete') {
                delete next[key];
            } else {
                next[key] = state.queue[key].value;
            }
        });

        var changed = JSON.stringify(next) !== JSON.stringify(state.cache || {});
        state.cache = next;
        return changed;
    }

    function emitRefreshed() {
        try {
            window.dispatchEvent(new CustomEvent('remote-storage:refreshed'));
        } catch (error) {
            /* Eski brauzerlar uchun (CustomEvent konstruktor yo'q) */
            try {
                var legacy = document.createEvent('Event');
                legacy.initEvent('remote-storage:refreshed', false, false);
                window.dispatchEvent(legacy);
            } catch (inner) {}
        }
    }

    function fetchBootstrap() {
        var url = state.endpoint + '?action=storage_bootstrap&t=' + Date.now();

        if (!window.fetch) {
            return new Promise(function (resolve, reject) {
                var xhr = new XMLHttpRequest();
                var timeout = setTimeout(function () {
                    xhr.abort();
                    reject(new Error('Storage bootstrap timeout'));
                }, state.bootstrapTimeoutMs);

                xhr.open('GET', url, true);
                xhr.onreadystatechange = function () {
                    if (xhr.readyState !== 4) {
                        return;
                    }

                    clearTimeout(timeout);

                    if (xhr.status >= 200 && xhr.status < 300) {
                        try {
                            resolve(JSON.parse(xhr.responseText || '{}'));
                        } catch (error) {
                            reject(error);
                        }
                        return;
                    }

                    reject(new Error('HTTP ' + xhr.status));
                };
                xhr.onerror = function () {
                    clearTimeout(timeout);
                    reject(new Error('Storage bootstrap network error'));
                };
                xhr.send(null);
            });
        }

        return new Promise(function (resolve, reject) {
            var controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
            var timeoutId = setTimeout(function () {
                if (controller) {
                    controller.abort();
                }
                reject(new Error('Storage bootstrap timeout'));
            }, state.bootstrapTimeoutMs);

            fetch(url, {
                cache: 'no-store',
                signal: controller ? controller.signal : undefined,
            }).then(function (response) {
                if (!response.ok) {
                    throw new Error('HTTP ' + response.status);
                }

                return response.json().catch(function () {
                    return {};
                });
            }).then(resolve).catch(reject).finally(function () {
                clearTimeout(timeoutId);
            });
        });
    }

    function bootstrap() {
        if (!canPatchStorage || state.ready) {
            state.ready = true;
            return Promise.resolve(state);
        }

        if (state.bootstrapPromise) {
            return state.bootstrapPromise;
        }

        /* 1-qadam — SURAT. Bo'lsa, tarmoqni umuman kutmaymiz: ilova shu
           zahoti chizila boshlaydi. Sahifa ochilgandan buyon yozilgan
           qiymatlar (agar bo'lsa) suratdan ustun turadi. */
        var snapshot = readSnapshot();
        var instant = false;

        if (snapshot) {
            state.cache = Object.assign({}, snapshot, state.cache || {});
            state.ready = true;
            instant = true;
            restorePendingBackups();
            migrateLegacyLocalStorage();
            logger.info('Storage snapshot loaded instantly', {
                keys: cacheKeys().length,
            });
        }

        /* 2-qadam — SERVER. Surat bo'lsa bu ORQA FONDA ketadi va hech kim
           uni kutmaydi; bo'lmasa (birinchi kirish) eski xatti-harakat. */
        var network = fetchBootstrap().then(function (json) {
            var changed = false;

            if (instant) {
                changed = applyServerItems(json.items);
            } else {
                var localWrites = state.cache || {};
                state.cache = Object.assign({}, json.items || {}, localWrites);
                state.ready = true;
                restorePendingBackups();
                migrateLegacyLocalStorage();
            }

            writeSnapshot();
            logger.info('Server storage loaded', {
                keys: cacheKeys().length,
            });

            if (instant && changed) {
                emitRefreshed();
            }

            return state;
        }).catch(function (error) {
            state.ready = true;
            state.cache = state.cache || {};

            /* Surat BOR bo'lsa xotira rejimiga o'tmaymiz: ma'lumot to'g'ri,
               shunchaki internet yo'q. Yozuvlar navbatda qolib, ulanish
               tiklanganda yuboriladi. Surat bo'lmagandagina (hech narsa
               bilmaymiz) eski xavfsiz rejimga tushamiz. */
            if (!instant) {
                state.syncEnabled = false;
                migrateLegacyLocalStorage();
            }

            logger.error('Server storage bootstrap failed', {
                error: error.message,
                offlineWithSnapshot: instant,
            });

            return state;
        });

        state.bootstrapPromise = instant ? Promise.resolve(state) : network;
        return state.bootstrapPromise;
    }

    function whenReady() {
        return bootstrap();
    }

    function scheduleFlush(delay) {
        if (!state.syncEnabled) {
            return;
        }

        clearTimeout(state.flushTimer);
        state.flushTimer = setTimeout(flushQueue, typeof delay === 'number' ? delay : 180);
    }

    function buildOps() {
        return Object.keys(state.queue).map(function (key) {
            return {
                key: key,
                type: state.queue[key].type,
                value: state.queue[key].value,
                stamp: state.queue[key].stamp || 0,
            };
        });
    }

    function restoreOps(ops) {
        ops.forEach(function (item) {
            if (!Object.prototype.hasOwnProperty.call(state.queue, item.key)) {
                state.queue[item.key] = {
                    type: item.type,
                    value: item.value,
                    stamp: normalizeStamp(item.stamp),
                };
            }
        });
    }

    function removeQueuedOps(ops) {
        ops.forEach(function (op) {
            if (op && Object.prototype.hasOwnProperty.call(state.queue, op.key)) {
                delete state.queue[op.key];
            }
        });
    }

    function flushQueue() {
        if (!state.syncEnabled) {
            return;
        }

        if (!state.ready) {
            bootstrap().then(function () {
                scheduleFlush(0);
            });
            return;
        }

        var ops = buildOps();
        if (!ops.length) {
            return;
        }

        state.queue = {};

        var payload = JSON.stringify({ ops: ops });
        var canUseKeepalive = payload.length < state.keepalivePayloadLimit;

        fetch(state.endpoint + '?action=storage_sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: payload,
            keepalive: canUseKeepalive,
        }).then(function (response) {
            if (!response.ok) {
                throw new Error('HTTP ' + response.status);
            }

            return response.json().catch(function () {
                return { success: true };
            });
        }).then(function (json) {
            if (json && json.success === false) {
                throw new Error(json.error || json.message || 'Storage sync rejected');
            }
            state.syncRetryDelayMs = 600;
            forgetPendingOps(ops);
        }).catch(function (error) {
            restoreOps(ops);

            logger.warn('Server storage sync failed, queue restored', {
                count: ops.length,
                error: error.message,
            });

            scheduleFlush(state.syncRetryDelayMs);
            state.syncRetryDelayMs = Math.min(state.maxSyncRetryDelayMs, state.syncRetryDelayMs * 2);
        });
    }

    function splitFinalOps(ops) {
        var chunks = [];
        var current = [];
        var deferred = [];

        ops.forEach(function (op) {
            if (!isKeepaliveSafe([op])) {
                deferred.push(op);
                return;
            }

            var next = current.concat([op]);
            if (current.length && !isKeepaliveSafe(next)) {
                chunks.push(current);
                current = [op];
                return;
            }

            current = next;
        });

        if (current.length) {
            chunks.push(current);
        }

        return {
            chunks: chunks,
            deferred: deferred,
        };
    }

    function sendFinalChunk(ops) {
        var payload = JSON.stringify({ ops: ops });

        if (navigator.sendBeacon) {
            var blob = new Blob([payload], { type: 'application/json' });
            if (navigator.sendBeacon(state.endpoint + '?action=storage_sync', blob)) {
                removeQueuedOps(ops);
                forgetPendingOps(ops);
                return true;
            }
        }

        if (window.fetch) {
            fetch(state.endpoint + '?action=storage_sync', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: payload,
                keepalive: true,
            }).catch(function (error) {
                restoreOps(ops);
                logger.warn('Final Server storage sync failed', {
                    count: ops.length,
                    error: error.message,
                });
            });
            removeQueuedOps(ops);
            forgetPendingOps(ops);
            return true;
        }

        return false;
    }

    function flushQueueSync() {
        if (!state.syncEnabled) {
            return;
        }

        var ops = buildOps();
        if (!ops.length) {
            return;
        }

        try {
            if (isKeepaliveSafe(ops) && sendFinalChunk(ops)) {
                return;
            }

            var split = splitFinalOps(ops);
            split.deferred.forEach(function (op) {
                if (op.type === 'set') {
                    rememberPendingOp(op);
                }
            });
            split.chunks.forEach(sendFinalChunk);

            if (split.deferred.length) {
                logger.warn('Large storage ops kept for next startup sync', {
                    count: split.deferred.length,
                });
            }
        } catch (error) {
            logger.warn('Final Server storage sync failed', {
                count: ops.length,
                error: error.message,
            });
        }
    }

    if (canPatchStorage) {
        Storage.prototype.getItem = function (key) {
            if (!isLocalStorageTarget(this)) {
                return nativeGetItem.call(this, key);
            }

            /* ICHKI KALIT (`__remote_storage_` prefiksi) — masofaviy qatlam
               umuman aralashmaydi: to'g'ridan-to'g'ri brauzer xotirasidan.
               Bu kalitlar QURILMAGA tegishli (kesh, navbat surati) va
               serverga yuborilmasligi kerak. */
            if (isInternalKey(key)) {
                return nativeGetItem.call(window.localStorage, key);
            }

            if (!state.ready) {
                bootstrap();
            }

            if (Object.prototype.hasOwnProperty.call(state.cache, key)) {
                return state.cache[key];
            }

            if (!state.ready) {
                return nativeGetItem.call(window.localStorage, key);
            }

            if (!state.syncEnabled) {
                return nativeGetItem.call(window.localStorage, key);
            }

            return null;
        };

        Storage.prototype.setItem = function (key, value) {
            var stringValue = toStringValue(value);
            var stamp = makeStamp();

            if (!isLocalStorageTarget(this)) {
                return nativeSetItem.call(this, key, stringValue);
            }

            /* ICHKI KALIT — serverga YUBORILMAYDI.
               Ilgari bu tekshiruv FAQAT o'qishda (`listNativeKeys`) bor edi,
               yozishda esa yo'q edi. Natijada `__remote_storage_` prefiksli
               kalit ham `app_storage` ga tushardi: bosh sahifa lentasining
               2.3 MB lik keshi shu yo'l bilan bazaga yozilib, har ochilishda
               `storage_bootstrap` ni 4.5 soniyalik chegaradan chiqarardi.
               Bootstrap yiqilsa `state.cache` bo'sh qoladi va HAMMA sozlama
               (o'rgangan so'zlar ham) "saqlanmagandek" ko'rinardi. */
            if (isInternalKey(key)) {
                return nativeSetItem.call(window.localStorage, key, stringValue);
            }

            if (!state.ready) {
                bootstrap();
            }

            state.cache[key] = stringValue;
            rememberKeyVersion(key, stamp);
            /* Surat yangilanib boradi — keyingi ochilishda ilova aynan shu
               holatni tarmoqsiz, darhol ko'rsatadi. */
            scheduleSnapshot();

            if (state.syncEnabled) {
                state.queue[key] = {
                    type: 'set',
                    value: stringValue,
                    stamp: stamp,
                };
                broadcastStorageOp({
                    key: key,
                    type: 'set',
                    value: stringValue,
                    stamp: stamp,
                });

                if (stringValue.length > state.largeValueThreshold || isLargeSetOp(state.queue[key])) {
                    rememberPendingOp({
                        key: key,
                        type: 'set',
                        value: stringValue,
                        stamp: stamp,
                    });
                    flushQueue();
                } else {
                    forgetPendingKey(key);
                    scheduleFlush();
                }
            } else {
                nativeSetItem.call(window.localStorage, key, stringValue);
                broadcastStorageOp({
                    key: key,
                    type: 'set',
                    value: stringValue,
                    stamp: stamp,
                });
            }
        };

        Storage.prototype.removeItem = function (key) {
            var stamp = makeStamp();

            if (!isLocalStorageTarget(this)) {
                return nativeRemoveItem.call(this, key);
            }

            /* Ichki kalit — o'chirish ham faqat shu qurilmada */
            if (isInternalKey(key)) {
                return nativeRemoveItem.call(window.localStorage, key);
            }

            if (!state.ready) {
                bootstrap();
            }

            delete state.cache[key];
            rememberKeyVersion(key, stamp);
            forgetPendingKey(key);
            scheduleSnapshot();

            if (state.syncEnabled) {
                state.queue[key] = {
                    type: 'delete',
                    value: null,
                    stamp: stamp,
                };
                broadcastStorageOp({
                    key: key,
                    type: 'delete',
                    value: null,
                    stamp: stamp,
                });
                scheduleFlush();
            } else {
                nativeRemoveItem.call(window.localStorage, key);
                broadcastStorageOp({
                    key: key,
                    type: 'delete',
                    value: null,
                    stamp: stamp,
                });
            }
        };

        Storage.prototype.clear = function () {
            var stamp = makeStamp();

            if (!isLocalStorageTarget(this)) {
                return nativeClear.call(this);
            }

            if (!state.ready) {
                bootstrap();
            }

            cacheKeys().forEach(function (key) {
                rememberKeyVersion(key, stamp);
                if (state.syncEnabled) {
                    state.queue[key] = {
                        type: 'delete',
                        value: null,
                        stamp: stamp,
                    };
                }
            });

            state.cache = {};
            writePendingOps([]);
            /* Surat ham darhol tozalanadi — aks holda sahifa yangilanganda
               endigina o'chirilgan ma'lumot suratdan qaytib kelardi. */
            try {
                if (canPatchStorage) {
                    nativeRemoveItem.call(window.localStorage, snapshotKey);
                }
            } catch (error) {}
            state.clearStamp = stamp;
            broadcastStorageMessage({
                kind: 'storage-clear',
                stamp: stamp,
            });

            if (state.syncEnabled) {
                scheduleFlush();
            } else {
                nativeClear.call(window.localStorage);
            }
        };

        Storage.prototype.key = function (index) {
            if (!isLocalStorageTarget(this)) {
                return nativeKey.call(this, index);
            }

            if (!state.ready) {
                bootstrap();
            }

            var keys = cacheKeys();
            if (!state.syncEnabled) {
                return nativeKey.call(window.localStorage, index);
            }

            return typeof keys[index] === 'undefined' ? null : keys[index];
        };

        try {
            Object.defineProperty(Storage.prototype, 'length', {
                configurable: true,
                enumerable: nativeLengthDescriptor ? nativeLengthDescriptor.enumerable : true,
                get: function () {
                    if (!isLocalStorageTarget(this)) {
                        return nativeLengthDescriptor && nativeLengthDescriptor.get
                            ? nativeLengthDescriptor.get.call(this)
                            : 0;
                    }

                    if (!state.ready) {
                        bootstrap();
                    }

                    if (!state.ready || !state.syncEnabled) {
                        var nativeLength = nativeLengthDescriptor && nativeLengthDescriptor.get
                            ? nativeLengthDescriptor.get.call(window.localStorage)
                            : listNativeKeys().length;
                        return Math.max(cacheKeys().length, nativeLength);
                    }

                    return cacheKeys().length;
                },
            });
        } catch (error) {
            logger.warn('Storage.length could not be patched', {
                error: error.message,
            });
        }

    }

    document.addEventListener('visibilitychange', function () {
        if (document.visibilityState === 'hidden') {
            flushQueueSync();
        } else if (document.visibilityState === 'visible') {
            scheduleFlush(0);
        }
    });
    window.addEventListener('pagehide', flushQueueSync);
    window.addEventListener('beforeunload', flushQueueSync);

    /* Qayta ulanish: birinchi urinish muvaffaqiyatsiz bo'lsa (masalan hali tizimga
       kirilmagan bo'lsa) sinxronlash butun sessiya davomida o'chib qolardi. Kirgandan
       keyin shu funksiya chaqiriladi va bog'lanish qaytadan quriladi. */
    function reset() {
        state.bootstrapPromise = null;
        state.ready = false;
        state.syncEnabled = true;
        return bootstrap();
    }

    /* ---------- FAQAT SHU QURILMADA qoladigan qiymatlar ----------
       Ba'zi narsalar serverga sinxronlanmasligi kerak, lekin sahifa
       yangilanganda ham saqlanishi shart (masalan oxirgi kirish holati:
       auth.js undan foydalanib ilovani serverni KUTMASDAN ochadi).
       Oddiy `localStorage` bu yerda yaramaydi — u butunlay shu ko'prik
       ostida va har yozuv serverga ketadi. Shuning uchun ichki kalit
       ostida TO'G'RIDAN-TO'G'RI brauzer xotirasiga yozamiz: `__remote_storage_`
       prefiksi tufayli `isInternalKey()` uni ichki deb biladi, ya'ni
       sinxronlashga ham, `purgeNativeStorage()` ga ham tushmaydi. */
    var localOnlyPrefix = '__remote_storage_local_';

    function localOnlyGet(name) {
        if (!canPatchStorage) return null;
        try {
            return nativeGetItem.call(window.localStorage, localOnlyPrefix + name);
        } catch (error) { return null; }
    }

    function localOnlySet(name, value) {
        if (!canPatchStorage) return;
        try {
            if (value === null || value === undefined) {
                nativeRemoveItem.call(window.localStorage, localOnlyPrefix + name);
            } else {
                nativeSetItem.call(window.localStorage, localOnlyPrefix + name, String(value));
            }
        } catch (error) {}
    }

    window.RemoteStorageBridge = {
        bootstrap: bootstrap,
        whenReady: whenReady,
        reset: reset,
        flush: flushQueue,
        flushSync: flushQueueSync,
        state: state,
        localGet: localOnlyGet,
        localSet: localOnlySet,
    };

    setupTabSync();
    bootstrap();
})();
