/**
 * Formats an event's start/end as "15 Ağustos 2026 15:00 – 17:00" when both fall on the
 * same day, or "15 Ağustos 2026 15:00 – 16 Ağustos 2026 09:00" when the event spans days.
 * Shared by the detail page and the map's hover tooltip so this logic exists once.
 */
export function formatEventRange(startsAt: string, endsAt: string): string {
  const start = new Date(startsAt);
  const end = new Date(endsAt);
  const dateFormat: Intl.DateTimeFormatOptions = {
    day: "numeric",
    month: "long",
    year: "numeric",
  };
  const timeFormat: Intl.DateTimeFormatOptions = { hour: "2-digit", minute: "2-digit" };

  const startDate = start.toLocaleDateString("tr-TR", dateFormat);
  const startTime = start.toLocaleTimeString("tr-TR", timeFormat);
  const endTime = end.toLocaleTimeString("tr-TR", timeFormat);

  if (start.toDateString() === end.toDateString()) {
    return `${startDate} ${startTime} – ${endTime}`;
  }
  const endDate = end.toLocaleDateString("tr-TR", dateFormat);
  return `${startDate} ${startTime} – ${endDate} ${endTime}`;
}
