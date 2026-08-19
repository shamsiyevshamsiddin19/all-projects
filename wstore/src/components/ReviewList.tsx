import { Star } from "lucide-react";
import { ReviewItem } from "@/lib/types";

function initials(name: string | null): string {
  if (!name) return "?";
  return name.trim().charAt(0).toUpperCase();
}

export default function ReviewList({ reviews }: { reviews: ReviewItem[] }) {
  return (
    <div className="flex flex-col gap-4">
      {reviews.map((r) => (
        <div
          key={r.id}
          className="rounded-card border border-border bg-surface p-4"
        >
          <div className="flex items-center gap-3">
            {r.userImage ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={r.userImage}
                alt={r.userName ?? ""}
                className="h-8 w-8 rounded-full object-cover"
              />
            ) : (
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-surface-2 text-sm font-semibold text-muted">
                {initials(r.userName)}
              </span>
            )}
            <div>
              <div className="text-sm font-medium text-fg">
                {r.userName ?? "Foydalanuvchi"}
              </div>
              <div className="flex items-center gap-0.5">
                {[1, 2, 3, 4, 5].map((i) => (
                  <Star
                    key={i}
                    size={12}
                    className={
                      i <= r.rating
                        ? "fill-gold text-gold"
                        : "fill-none text-border-strong"
                    }
                  />
                ))}
              </div>
            </div>
          </div>
          <p className="mt-3 whitespace-pre-line text-sm leading-6 text-fg/90">
            {r.comment}
          </p>
        </div>
      ))}
    </div>
  );
}
