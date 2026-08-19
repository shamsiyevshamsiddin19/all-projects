"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, CheckCircle2, UploadCloud, AlertTriangle } from "lucide-react";
import { CATEGORIES } from "@/lib/mock-data";
import { WEBSITE_SUBCATS, type WebsiteSubcat } from "@/lib/types";
import { useT, type TKey } from "@/components/Providers";

const SUBCAT_TKEY: Record<WebsiteSubcat, TKey> = {
  portfolio: "subPortfolio",
  teacher: "subTeacher",
  edu: "subEdu",
  pharmacy: "subPharmacy",
  restaurant: "subRestaurant",
  other: "subOther",
};

export interface ProductFormInitial {
  id: string;
  title: string;
  price: number;
  categorySlug: string;
  subcategory: string | null;
  description: string;
  techStack: string[];
  features: string[];
  coverImage: string;
  screenshots?: string[];
  demoUrl: string | null;
  telegramUsername: string | null;
  hasFile?: boolean;
}

export default function ProductForm({
  initial,
}: {
  initial?: ProductFormInitial;
}) {
  const router = useRouter();
  const t = useT();
  const isEdit = Boolean(initial);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [categorySlug, setCategorySlug] = useState(
    initial?.categorySlug ?? CATEGORIES[0].key,
  );
  const [fileName, setFileName] = useState<string | null>(null);
  const [fileKey, setFileKey] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);

  const [coverImage, setCoverImage] = useState<string>(initial?.coverImage ?? "");
  const [screenshots, setScreenshots] = useState<string[]>(initial?.screenshots ?? []);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [imageError, setImageError] = useState<string | null>(null);

  async function handleImageUpload(e: React.ChangeEvent<HTMLInputElement>, type: "cover" | "screenshot") {
    const f = e.target.files?.[0];
    if (!f) return;
    setImageError(null);
    setUploadingImage(true);
    try {
      const uploadFd = new FormData();
      uploadFd.append("file", f);
      const res = await fetch("/api/upload-image", { method: "POST", body: uploadFd });
      const data = await res.json();
      if (!res.ok || !data.url) {
        throw new Error(data.error ?? "Rasm yuklashda xatolik");
      }
      if (type === "cover") {
        setCoverImage(data.url);
      } else {
        setScreenshots((s) => [...s, data.url]);
      }
    } catch (err) {
      setImageError(err instanceof Error ? err.message : "Xatolik yuz berdi");
    } finally {
      setUploadingImage(false);
      e.target.value = ""; // reset file input
    }
  }

  function removeScreenshot(index: number) {
    setScreenshots(screenshots.filter((_, i) => i !== index));
  }

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    setFileName(f.name);
    setFileError(null);
    setFileKey(null);
    setUploading(true);
    try {
      const uploadFd = new FormData();
      uploadFd.append("file", f);
      const res = await fetch("/api/upload", { method: "POST", body: uploadFd });
      const data = await res.json();
      if (!res.ok || !data.fileKey) {
        throw new Error(data.error ?? "Fayl yuklashda xatolik");
      }
      setFileKey(data.fileKey);
    } catch (err) {
      setFileError(err instanceof Error ? err.message : "Xatolik yuz berdi");
      setFileName(null);
    } finally {
      setUploading(false);
    }
  }

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);

    if (!isEdit && !fileKey) {
      setError(
        "Avval mahsulot faylini (.zip) yuklang — xaridor to'lovdan so'ng shu faylni oladi.",
      );
      return;
    }

    const fd = new FormData(e.currentTarget);
    if (!isEdit && screenshots.length === 0) {
      setError(
        "Kamida bitta skrinshot yuklang — xaridorlar mahsulotni ko'rib xarid qilishadi.",
      );
      return;
    }

    if (!coverImage) {
      setError("Muqova rasm yuklash majburiy.");
      return;
    }

    setLoading(true);

    const payload = {
      title: fd.get("title"),
      price: fd.get("price"),
      categorySlug: fd.get("categorySlug"),
      subcategory: fd.get("subcategory") || null,
      description: fd.get("description"),
      techStack: fd.get("techStack"),
      features: fd.get("features"),
      coverImage: coverImage,
      screenshots: screenshots,
      demoUrl: fd.get("demoUrl"),
      telegramUsername: fd.get("telegramUsername"),
      ...(fileKey ? { fileKey } : {}),
    };

    const url = isEdit ? `/api/products/${initial!.id}` : "/api/products";
    const method = isEdit ? "PATCH" : "POST";

    const res = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    setLoading(false);
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      setError(data.error ?? "Xatolik yuz berdi");
      return;
    }
    router.push("/seller");
    router.refresh();
  }

  return (
    <form onSubmit={onSubmit} className="max-w-xl space-y-4">
      <Field
        name="title"
        label="Nomi"
        placeholder="Telegram Do'kon Boti"
        defaultValue={initial?.title}
        required
      />

      <div className="grid grid-cols-2 gap-4">
        <Field
          name="price"
          label="Narx ($)"
          type="number"
          placeholder="29"
          defaultValue={initial?.price}
          required
        />
        <div>
          <Label>Kategoriya</Label>
          <select
            name="categorySlug"
            required
            value={categorySlug}
            onChange={(e) => setCategorySlug(e.target.value)}
            className="w-full rounded-lg border border-border bg-surface px-3 py-2.5 text-sm text-fg outline-none focus:border-accent"
          >
            {CATEGORIES.map((c) => (
              <option key={c.key} value={c.key}>
                {c.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {categorySlug === "website" && (
        <div>
          <Label>Sayt yo&apos;nalishi</Label>
          <select
            name="subcategory"
            defaultValue={initial?.subcategory ?? ""}
            className="w-full rounded-lg border border-border bg-surface px-3 py-2.5 text-sm text-fg outline-none focus:border-accent"
          >
            <option value="">{t("subAll")}</option>
            {WEBSITE_SUBCATS.map((s) => (
              <option key={s} value={s}>
                {t(SUBCAT_TKEY[s])}
              </option>
            ))}
          </select>
        </div>
      )}

      <div>
        <Label>Tavsif</Label>
        <textarea
          name="description"
          rows={4}
          placeholder="Mahsulot haqida qisqacha..."
          defaultValue={initial?.description}
          className="w-full rounded-lg border border-border bg-surface px-3 py-2.5 text-sm text-fg outline-none focus:border-accent"
        />
      </div>

      <div>
        <Label>Xususiyatlar (har qatorda bittadan)</Label>
        <textarea
          name="features"
          rows={4}
          placeholder={"To'liq manba kodi\nResponsive dizayn\nAdmin panel"}
          defaultValue={initial?.features?.join("\n")}
          className="w-full rounded-lg border border-border bg-surface px-3 py-2.5 text-sm text-fg outline-none focus:border-accent"
        />
      </div>

      <Field
        name="techStack"
        label="Texnologiyalar (vergul bilan)"
        placeholder="Python, Telegram"
        defaultValue={initial?.techStack?.join(", ")}
      />

      <div>
        <Label>Muqova rasm <span className="text-red-400">*</span></Label>
        <label className="flex cursor-pointer items-center gap-2.5 rounded-lg border border-dashed border-border-strong bg-surface px-3 py-2.5 text-sm text-muted transition hover:border-accent hover:text-fg">
          <UploadCloud size={16} className="shrink-0" />
          <span className="truncate">Rasm tanlash (JPG, PNG, WEBP)</span>
          <input
            type="file"
            accept="image/jpeg, image/png, image/webp"
            className="sr-only"
            onChange={(e) => handleImageUpload(e, "cover")}
            disabled={uploadingImage}
          />
        </label>
        {coverImage && (
          <div className="mt-2">
            <img src={coverImage} alt="Cover" className="h-20 w-auto rounded border border-border object-cover" />
          </div>
        )}
      </div>

      <div>
        <Label>
          Skrinshotlar
          {!isEdit && <span className="text-red-400"> *</span>}
        </Label>
        <p className="mb-2 text-xs text-muted">
          Xaridorlar mahsulot sahifasida shu rasmlarni galereya sifatida
          ko&apos;radi.
        </p>
        <label className="flex cursor-pointer items-center gap-2.5 rounded-lg border border-dashed border-border-strong bg-surface px-3 py-2.5 text-sm text-muted transition hover:border-accent hover:text-fg">
          <UploadCloud size={16} className="shrink-0" />
          <span className="truncate">Skrinshot qo'shish</span>
          <input
            type="file"
            accept="image/jpeg, image/png, image/webp"
            className="sr-only"
            onChange={(e) => handleImageUpload(e, "screenshot")}
            disabled={uploadingImage}
          />
        </label>
        {screenshots.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {screenshots.map((s, i) => (
              <div key={i} className="relative group">
                <img src={s} alt={`Screenshot ${i}`} className="h-16 w-16 rounded border border-border object-cover" />
                <button
                  type="button"
                  onClick={() => removeScreenshot(i)}
                  className="absolute -right-2 -top-2 rounded-full bg-red-500 p-1 text-white opacity-0 transition group-hover:opacity-100"
                >
                  <AlertTriangle size={10} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {imageError && (
        <p className="text-sm text-red-400">{imageError}</p>
      )}
      <Field
        name="demoUrl"
        label="Demo havola (ixtiyoriy)"
        placeholder="https://..."
        defaultValue={initial?.demoUrl ?? undefined}
      />
      <Field
        name="telegramUsername"
        label="Telegram username (buyurtmalar shu yerga keladi)"
        placeholder="username"
        defaultValue={initial?.telegramUsername ?? undefined}
      />

      <div>
        <Label>
          Mahsulot fayli (.zip){!isEdit && <span className="text-red-400"> *</span>}
        </Label>
        <p className="mb-2 text-xs text-muted">
          Xaridor to&apos;lov qilgandan so&apos;ng shu faylni avtomatik yuklab
          oladi. Manba kod / arxiv shu yerda yuklanadi — Telegram orqali
          alohida yuborish shart emas.
        </p>
        <label className="flex cursor-pointer items-center gap-2.5 rounded-lg border border-dashed border-border-strong bg-surface px-3 py-2.5 text-sm text-muted transition hover:border-accent hover:text-fg">
          <UploadCloud size={16} className="shrink-0" />
          <span className="truncate">
            {fileName ?? "Fayl tanlash (.zip)"}
          </span>
          <input
            type="file"
            accept=".zip"
            className="sr-only"
            onChange={handleFileChange}
          />
        </label>
        <div className="mt-1.5 flex items-center gap-1.5 text-xs">
          {uploading && (
            <span className="flex items-center gap-1.5 text-muted">
              <Loader2 size={13} className="animate-spin" /> Yuklanmoqda...
            </span>
          )}
          {!uploading && fileKey && (
            <span className="flex items-center gap-1.5 text-green-400">
              <CheckCircle2 size={13} /> Fayl yuklandi
            </span>
          )}
          {!uploading && fileError && (
            <span className="flex items-center gap-1.5 text-red-400">
              <AlertTriangle size={13} /> {fileError}
            </span>
          )}
          {!uploading && !fileKey && !fileError && isEdit && (
            <span
              className={`flex items-center gap-1.5 ${initial?.hasFile ? "text-muted" : "text-gold"}`}
            >
              {initial?.hasFile ? (
                <>
                  <CheckCircle2 size={13} /> Joriy fayl saqlangan (o&apos;zgartirish
                  uchun yangisini tanlang)
                </>
              ) : (
                <>
                  <AlertTriangle size={13} /> Fayl hali yuklanmagan — xaridorlar
                  hech narsa ololmaydi
                </>
              )}
            </span>
          )}
        </div>
      </div>

      {error && (
        <p className="rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-400">
          {error}
        </p>
      )}

      <button
        disabled={loading || uploading}
        className="flex items-center gap-2 rounded-lg bg-accent px-5 py-2.5 text-sm font-medium text-white transition hover:bg-accent-hover disabled:opacity-60"
      >
        {loading && <Loader2 size={16} className="animate-spin" />}
        {isEdit ? "O'zgarishlarni saqlash" : "Mahsulotni saqlash"}
      </button>
      {!isEdit && (
        <p className="text-xs text-muted">
          Saqlangach, loyihani e&apos;lon qilish uchun 5000 so&apos;m
          to&apos;lashingiz kerak bo&apos;ladi (Sotuvchi panelida).
        </p>
      )}
    </form>
  );
}

function Label({ children }: { children: React.ReactNode }) {
  return (
    <label className="mb-1.5 block text-sm text-muted">{children}</label>
  );
}

function Field({
  name,
  label,
  type = "text",
  placeholder,
  required,
  defaultValue,
}: {
  name: string;
  label: string;
  type?: string;
  placeholder?: string;
  required?: boolean;
  defaultValue?: string | number;
}) {
  return (
    <div>
      <Label>{label}</Label>
      <input
        name={name}
        type={type}
        placeholder={placeholder}
        required={required}
        defaultValue={defaultValue}
        className="w-full rounded-lg border border-border bg-surface px-3 py-2.5 text-sm text-fg outline-none placeholder:text-muted/60 focus:border-accent"
      />
    </div>
  );
}
