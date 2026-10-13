import React from 'react';
import Link from 'next/link';
import { Shield, ArrowLeft, Mail, AlertTriangle } from 'lucide-react';

export default function DmcaPage() {
  return (
    <div className="min-h-screen bg-space-950 py-8 px-4 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-cyan-400 transition-colors py-1.5 px-3 rounded-xl bg-space-900 border border-space-800"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Bosh sahifaga qaytish</span>
          </Link>
        </div>

        <div className="p-8 rounded-3xl bg-space-900/60 border border-space-800 shadow-glass space-y-6">
          <div className="flex items-center gap-3 text-cyan-400">
            <Shield className="w-8 h-8" />
            <h1 className="text-3xl font-extrabold text-white">DMCA & Mualliflik Huquqi Siyosati</h1>
          </div>

          <div className="p-4 rounded-2xl bg-amber-950/40 border border-amber-500/30 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-amber-200 leading-relaxed">
              <strong>Muhim bildirishnoma:</strong> RadioGlobe hech qanday audio yoki video fayllarni o'z serverlarida saqlamaydi yoki qayta uzatmaydi. Biz faqat ochiq va jamoatchilikka tegishli radiostansiyalar havolalari katalogi hisoblanamiz.
            </p>
          </div>

          <div className="space-y-4 text-sm text-slate-300 leading-relaxed">
            <h2 className="text-lg font-bold text-white">1. Huquqiy Maqom</h2>
            <p>
              RadioGlobe platformasi (radio.shamsiyev.uz) dunyo bo'ylab mavjud bo'lgan ochiq manbali
              (open-source va radio-browser hamjamiyati) radio havolalarini indekslovchi qidiruv va ko'rsatish
              tizimidir.
            </p>

            <h2 className="text-lg font-bold text-white">2. Shikoyat Qilish Tartibi (Takedown Notice)</h2>
            <p>
              Agar siz biror radiostansiyaning qonuniy mualliflik huquqi egasi bo'lsangiz va ushbu havola
              katalogimizdan olib tashlanishini istasangiz, iltimos, bizga quyidagi ma'lumotlarni yuboring:
            </p>
            <ul className="list-disc pl-5 space-y-1 text-slate-400 text-xs">
              <li>Stansiya nomi va bizning platformadagi havolasi (URL);</li>
              <li>Mualliflik huquqini tasdiqlovchi rasmiy ma'lumot;</li>
              <li>Bog'lanish uchun elektron pochta manzili yoki telefon raqami.</li>
            </ul>

            <h2 className="text-lg font-bold text-white">3. Bog'lanish</h2>
            <div className="p-4 rounded-xl bg-space-850 border border-space-800 flex items-center gap-3">
              <Mail className="w-5 h-5 text-cyan-400" />
              <div>
                <p className="text-xs text-slate-400">Rasmiy murojaat pochtasi:</p>
                <a
                  href="mailto:contact@shamsiyev.uz"
                  className="text-sm font-semibold text-cyan-400 hover:underline"
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
