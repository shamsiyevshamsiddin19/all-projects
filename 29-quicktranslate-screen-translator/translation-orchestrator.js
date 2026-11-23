/*
 * Deterministic primary/fallback coordinator.
 * Providers may finish in any order; the UI receives exactly one completion.
 */

export class TranslationOrchestrator {
    constructor(callback, isCancelled = () => false) {
        this._callback = callback;
        this._isCancelled = isCancelled;
        this._finished = false;
        this._primary = {settled: false, result: null, error: null};
        this._fallback = {settled: false, result: null, error: null};
    }

    start(primaryStart, fallbackStart) {
        // Start fallback first so synchronous providers cannot create a gap.
        fallbackStart((result, error) => this._settle('fallback', result, error));
        primaryStart((result, error) => this._settle('primary', result, error));
    }

    _settle(kind, result, error) {
        if (this._finished || this._isCancelled()) return;
        const state = kind === 'primary' ? this._primary : this._fallback;
        if (state.settled) return;
        state.settled = true;
        state.result = result || null;
        state.error = error || null;

        if (kind === 'primary' && state.result) {
            this._finish(state.result, null);
            return;
        }

        if (!this._primary.settled) return;
        if (this._primary.result) {
            this._finish(this._primary.result, null);
            return;
        }
        if (!this._fallback.settled) return;
        if (this._fallback.result) {
            this._finish(this._fallback.result, null);
            return;
        }
        this._finish(null, 'Tarjima xizmatlari vaqtincha javob bermadi. Qayta urinib ko‘ring.');
    }

    _finish(result, error) {
        if (this._finished || this._isCancelled()) return;
        this._finished = true;
        this._callback(result, error);
    }
}
