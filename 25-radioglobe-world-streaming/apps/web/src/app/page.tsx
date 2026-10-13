import { fetchCountries } from '@/lib/api';
import GlobeClientWrapper from '@/components/Globe/GlobeClientWrapper';
import FallbackCountryList from '@/components/Globe/FallbackCountryList';

export default async function HomePage() {
  const countries = await fetchCountries(250, false);

  return (
    <div className="flex flex-col">
      {/* 3D Interactive Globe Section */}
      <section className="relative w-full">
        <GlobeClientWrapper countries={countries} />
      </section>

      {/* SEO & Fallback Directory Section */}
      <FallbackCountryList countries={countries} />
    </div>
  );
}
