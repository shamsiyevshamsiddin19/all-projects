import {
  Bot,
  Globe,
  Smartphone,
  Puzzle,
  Palette,
  Package,
  LayoutTemplate,
  type LucideIcon,
} from "lucide-react";
import { ProductCategory } from "@/lib/types";

// Kategoriya -> lucide icon komponenti (emoji o'rniga)
export const CATEGORY_ICONS: Record<ProductCategory, LucideIcon> = {
  portfolio: LayoutTemplate,
  bot: Bot,
  website: Globe,
  app: Smartphone,
  code: Puzzle,
  uikit: Palette,
};

export function categoryIcon(cat: ProductCategory): LucideIcon {
  return CATEGORY_ICONS[cat] ?? Package;
}
