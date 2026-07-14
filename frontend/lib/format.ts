/** Small display formatters shared across the UI. */

export function formatINR(amount: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatDate(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

/** "660" minutes -> "11h", "90" -> "1h 30m", "45" -> "45m". */
export function formatDuration(minutes: number): string {
  const total = Math.round(minutes);
  const h = Math.floor(total / 60);
  const m = total % 60;
  if (h && m) return `${h}h ${m}m`;
  return h ? `${h}h` : `${m}m`;
}

/** Pick an emoji for a human-readable weather condition (e.g. "light rain"). */
export function weatherEmoji(condition: string): string {
  const c = condition.toLowerCase();
  if (c.includes("thunder") || c.includes("storm")) return "⛈️";
  if (c.includes("snow") || c.includes("sleet")) return "❄️";
  if (c.includes("rain") || c.includes("drizzle")) return "🌧️";
  if (c.includes("cloud") || c.includes("overcast")) return "☁️";
  if (c.includes("mist") || c.includes("fog") || c.includes("haze")) return "🌫️";
  if (c.includes("clear") || c.includes("sun")) return "☀️";
  return "🌤️";
}
