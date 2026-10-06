import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import Navbar from "@/components/Navbar";
import ProductForm from "./ProductForm";

export default function NewProductPage() {
  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-[1100px] px-6 py-10">
        <Link
          href="/seller"
          className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-accent"
        >
          <ArrowLeft size={15} /> Sotuvchi paneliga qaytish
        </Link>
        <h1 className="mb-6 mt-4 text-2xl font-bold text-fg">
          Yangi mahsulot
        </h1>
        <ProductForm />
      </main>
    </>
  );
}
