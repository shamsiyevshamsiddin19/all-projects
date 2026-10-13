'use client';

import dynamic from 'next/dynamic';
import { Country } from '@/types';

const GlobeMap = dynamic(() => import('@/components/Globe/GlobeMap'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-[calc(100vh-60px)] min-h-[580px] bg-space-950 flex flex-col items-center justify-center gap-4">
      <div className="w-16 h-16 rounded-full border-2 border-cyan-500/20 border-t-cyan-400 animate-spin" />
      <p className="text-xs font-mono text-cyan-400/80 tracking-widest uppercase">
        3D Globus yuklanmoqda...
      </p>
    </div>
  ),
});

interface GlobeClientWrapperProps {
  countries: Country[];
}

export default function GlobeClientWrapper({ countries }: GlobeClientWrapperProps) {
  return <GlobeMap countries={countries} />;
}
