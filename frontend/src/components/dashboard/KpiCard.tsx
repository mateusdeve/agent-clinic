import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

interface KpiCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  color: string; // tailwind bg class e.g. "bg-green-50"
  iconColor: string; // tailwind text class e.g. "text-green-600"
}

export function KpiCard({ label, value, icon: Icon, color, iconColor }: KpiCardProps) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 flex items-center gap-4">
      <div className={cn("rounded-lg p-3", color)}>
        <Icon className={cn("h-5 w-5", iconColor)} />
      </div>
      <div>
        <p className="text-sm text-gray-500">{label}</p>
        <p className="text-2xl font-semibold text-gray-800">{value}</p>
      </div>
    </div>
  );
}
