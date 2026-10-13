import React from 'react';
import Link from 'next/link';
import { Shield, ArrowLeft, Mail, AlertTriangle } from 'lucide-react';

export default function DmcaPage() {
  return (
    <div className="min-h-screen bg-void-950 py-8 px-4 lg:px-8 font-mono">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors py-1.5 px-3 bg-void-900 border border-void-750 hover:border-crimson"
          >
            <ArrowLeft className="w-3.5 h-3.5 text-crimson" />
            <span>[ RETURN TO GLOBE COMMAND ]</span>
          </Link>
        </div>

        <div className="tactical-box p-8 space-y-6 shadow-tactical-glass">
          <div className="flex items-center gap-3 text-crimson">
            <Shield className="w-8 h-8" />
            <h1 className="text-2xl sm:text-3xl font-black text-white tracking-wider uppercase">
              DMCA & MUALLIFLIK HUQUQI SIYOSATI
            </h1>
          </div>

          <div className="p-4 bg-void-950 border border-crimson/40 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-crimson flex-shrink-0 mt-0.5" />
            <p className="text-xs text-slate-300 leading-relaxed">
              <strong className="text-crimson-bright">[ MUHIM BILDIRISHNOMA ]:</strong> RadioGlobe hech qanday audio yoki video fayllarni o'z serverlarida saqlamaydi yoki qayta uzatmaydi. Biz faqat ochiq va jamoatchilikka tegishli radiostansiyalar havolalari katalogi hisoblanamiz.
            </p>
          </div>

          <div className="space-y-4 text-xs sm:text-sm text-slate-300 leading-relaxed">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider text-crimson-bright">
              1. Huquqiy Maqom
            </h2>
            <p>
              RadioGlobe platformasi (radio.shamsiyev.uz) dunyo bo'ylab mavjud bo'lgan ochiq manbali
              (open-source va radio-browser hamjamiyati) radio havolalarini indekslovchi qidiruv va ko'rsatish
              tizimidir.
            </p>

            <h2 className="text-sm font-bold text-white uppercase tracking-wider text-crimson-bright">
              2. Shikoyat Qilish Tartibi (Takedown Notice)
            </h2>
            <p>
              Agar siz biror radiostansiyaning qonuniy mualliflik huquqi egasi bo'lsangiz va ushbu havola
              katalogimizdan olib tashlanishini istasangiz, iltimos, bizga quyidagi ma'lumotlarni yuboring:
            </p>
            <ul className="list-disc pl-5 space-y-1 text-slate-400 text-xs">
              <li>Stansiya nomi va bizning platformadagi havolasi (URL);</li>
              <li>Mualliflik huquqini tasdiqlovchi rasmiy ma'lumot;</li>
              <li>Bog'lanish uchun elektron pochta manzili yoki telefon raqami.</li>
            </ul>

            <h2 className="text-sm font-bold text-white uppercase tracking-wider text-crimson-bright">
              3. Bog'lanish
            </h2>
            <div className="p-4 bg-void-950 border border-void-750 flex items-center gap-3">
              <Mail className="w-5 h-5 text-crimson" />
              <div>
                <p className="text-xs text-slate-400">Rasmiy murojaat pochtasi:</p>
                <a
                  href="mailto:contact@shamsiyev.uz"
                  className="text-sm font-semibold text-crimson hover:underline"
                >
                  contact@shamsiyev.uz
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
