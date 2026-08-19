// merged shared runtime

// merged from assets/js/shared/logger.js

(function () {
    if (window.AppLogger) {
        return;
    }

    var pageName = (location.pathname.split('/').pop() || 'app').trim() || 'app';
    var endpoint = '/api?action=log_client';

    function safeMeta(meta) {
        if (!meta) {
            return {};
        }

        try {
            return JSON.parse(JSON.stringify(meta));
        } catch (error) {
            return {
                stringify_error: error.message,
            };
        }
    }

    function shouldSend(level) {
        return level === 'warn' || level === 'error';
    }

    function shouldPrint(level) {
        return level === 'warn' || level === 'error';
    }

    function sendToServer(payload) {
        if (location.protocol === 'file:') {
            return;
        }

        try {
            var body = JSON.stringify(payload);

            if (navigator.sendBeacon) {
                var blob = new Blob([body], { type: 'application/json' });
                navigator.sendBeacon(endpoint, blob);
                return;
            }

            var xhr = new XMLHttpRequest();
            xhr.open('POST', endpoint, true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.send(body);
        } catch (error) {
            // Logger yuborishdagi xato asosiy app ishiga ta'sir qilmasin.
        }
    }

    function emit(level, message, meta) {
        var payload = {
            level: level,
            page: pageName,
            message: message,
            meta: safeMeta(meta),
            url: location.href,
            timestamp: new Date().toISOString(),
        };

        if (shouldPrint(level)) {
            var method = level === 'error' ? 'error' : 'warn';
            console[method]('[APP ' + level.toUpperCase() + '][' + pageName + '] ' + message, payload.meta);
        }

        if (shouldSend(level)) {
            sendToServer(payload);
        }
    }

    window.AppLogger = {
        debug: function (message, meta) {
            emit('debug', message, meta);
        },
        info: function (message, meta) {
            emit('info', message, meta);
        },
        warn: function (message, meta) {
            emit('warn', message, meta);
        },
        error: function (message, meta) {
            emit('error', message, meta);
        },
    };

    window.addEventListener('error', function (event) {
        window.AppLogger.error('JS xatosi aniqlandi', {
            message: event.message,
            file: event.filename,
            line: event.lineno,
            column: event.colno,
        });
    });

    window.addEventListener('unhandledrejection', function (event) {
        window.AppLogger.error('Promise xatosi aniqlandi', {
            reason: event.reason && event.reason.message ? event.reason.message : String(event.reason),
        });
    });

    if (window.fetch && !window.fetch.__appLoggerWrapped) {
        var nativeFetch = window.fetch.bind(window);

        window.fetch = function (input, init) {
            var startedAt = Date.now();
            var url = typeof input === 'string' ? input : (input && input.url ? input.url : 'unknown');
            var method = (init && init.method) || 'GET';
            var lowerUrl = String(url).toLowerCase();
            var silent = lowerUrl.indexOf('action=log_client') !== -1;
            var storageCall = lowerUrl.indexOf('action=storage_sync') !== -1 || lowerUrl.indexOf('action=storage_bootstrap') !== -1;

            if (!silent && !storageCall) {
                window.AppLogger.info('Fetch boshlandi', {
                    method: method,
                    url: url,
                });
            }

            return nativeFetch(input, init)
                .then(function (response) {
                    if (!silent) {
                        var meta = {
                            method: method,
                            url: url,
                            status: response.status,
                            duration_ms: Date.now() - startedAt,
                        };

                        if (response.ok) {
                            if (!storageCall) {
                                window.AppLogger.info('Fetch tugadi', meta);
                            }
                        } else {
                            window.AppLogger.warn('Fetch noto‘g‘ri javob qaytardi', meta);
                        }
                    }

                    return response;
                })
                .catch(function (error) {
                    if (!silent) {
                        window.AppLogger.error('Fetch muvaffaqiyatsiz tugadi', {
                            method: method,
                            url: url,
                            duration_ms: Date.now() - startedAt,
                            error: error.message,
                        });
                    }

                    throw error;
                });
        };

        window.fetch.__appLoggerWrapped = true;
    }

    window.AppLogger.info('Logger ishga tushdi');
})();
