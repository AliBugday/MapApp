export interface ReportImage {
  id: number;
  url: string;
  thumbnail_url: string;
}

export interface Report {
  id: number;
  title: string;
  description: string;
  status: "open" | "in_progress" | "resolved" | "rejected";
  type: "issue" | "request" | "announcement" | "event";
  visibility: "public" | "members";
  /** Only present for type="event"; null otherwise. */
  event_starts_at: string | null;
  event_ends_at: string | null;
  latitude: number;
  longitude: number;
  author_username: string | null;
  organization_name: string | null;
  upvote_count: number;
  comment_count: number;
  /** Whether the *current* user has upvoted; always present, false when anonymous. */
  has_upvoted: boolean;
  rsvp_count: number;
  /** Whether the *current* user has RSVPed; always present, false when anonymous. */
  has_rsvped: boolean;
  images: ReportImage[];
  created_at: string;
  updated_at: string;
}

export interface Comment {
  id: number;
  body: string;
  author_username: string;
  created_at: string;
}

/** What the upvote endpoint returns, for reconciling an optimistic update. */
export interface UpvoteState {
  upvote_count: number;
  has_upvoted: boolean;
}

/** What the rsvp endpoint returns, for reconciling an optimistic update. */
export interface RsvpState {
  rsvp_count: number;
  has_rsvped: boolean;
}

export interface User {
  id: number;
  username: string;
  email: string;
  organization_name: string | null;
  organization_kind: "municipality" | "public" | null;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function readCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS", "TRACE"]);

/**
 * The single place that knows about Django's CSRF requirement.
 *
 * Requests go to relative URLs so Next.js proxies them to Django on the same
 * origin; unsafe methods carry the csrftoken cookie back as an X-CSRFToken header.
 * No component should call fetch() against the API directly.
 */
export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const method = (options.method ?? "GET").toUpperCase();
  const headers = new Headers(options.headers);

  // FormData (image uploads) must NOT get a Content-Type set here — fetch sets its own,
  // including the multipart boundary, only when the header is left unset.
  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (!SAFE_METHODS.has(method)) {
    const token = readCookie("csrftoken");
    if (token) headers.set("X-CSRFToken", token);
  }

  const response = await fetch(path, { ...options, method, headers, credentials: "same-origin" });

  if (!response.ok) {
    throw new ApiError(await describeError(response), response.status);
  }
  return response.status === 204 ? (undefined as T) : ((await response.json()) as T);
}

// Only the handful of field names that actually appear in a form on this site need a
// human label; anything else falls back to the raw key rather than growing this table
// for fields no user ever sees an error for.
const FIELD_LABELS: Record<string, string> = {
  username: "Kullanıcı adı",
  password: "Şifre",
  title: "Başlık",
  description: "Açıklama",
  body: "Yorum",
  type: "Tür",
  visibility: "Görünürlük",
  image: "Görsel",
  event_starts_at: "Başlangıç zamanı",
  event_ends_at: "Bitiş zamanı",
};

async function describeError(response: Response): Promise<string> {
  if (response.status === 403) {
    return "Bunu yapmak için giriş yapmış olmanız gerekir.";
  }
  try {
    const body = await response.json();
    // DRF's own errors ("detail") are already written for a human — and, with
    // LANGUAGE_CODE="tr" on the backend, already in Turkish. Field errors are keyed by
    // field name, which is worth showing so the user knows what to fix.
    if (typeof body.detail === "string") {
      return body.detail;
    }
    const firstField = Object.entries(body)[0];
    if (firstField) {
      const [field, messages] = firstField;
      const label = FIELD_LABELS[field] ?? field;
      return `${label}: ${Array.isArray(messages) ? messages.join(", ") : String(messages)}`;
    }
  } catch {
    // Fall through to the generic message below.
  }
  return `İstek başarısız oldu (${response.status})`;
}

/**
 * Who is signed in, or null.
 *
 * Also the call that seeds Django's csrftoken cookie (the endpoint sets it), so the
 * frontend must make this request before any POST can succeed.
 */
export async function fetchMe(): Promise<User | null> {
  const { user } = await apiFetch<{ user: User | null }>("/api/auth/me/");
  return user;
}

export function register(input: { username: string; password: string }): Promise<User> {
  return apiFetch<User>("/api/auth/register/", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function login(input: { username: string; password: string }): Promise<User> {
  return apiFetch<User>("/api/auth/login/", { method: "POST", body: JSON.stringify(input) });
}

export function logout(): Promise<void> {
  return apiFetch<void>("/api/auth/logout/", { method: "POST" });
}

/**
 * Add or remove the current user's upvote.
 *
 * Both directions are idempotent server-side, so a retry after a failed request is
 * safe and cannot double-count.
 */
export function setUpvote(reportId: number, upvoted: boolean): Promise<UpvoteState> {
  return apiFetch<UpvoteState>(`/api/reports/${reportId}/upvote/`, {
    method: upvoted ? "POST" : "DELETE",
  });
}

/**
 * Add or remove the current user's RSVP to an event.
 *
 * Both directions are idempotent server-side, so a retry after a failed request is
 * safe and cannot double-count.
 */
export function setRsvp(reportId: number, attending: boolean): Promise<RsvpState> {
  return apiFetch<RsvpState>(`/api/reports/${reportId}/rsvp/`, {
    method: attending ? "POST" : "DELETE",
  });
}

export function fetchReport(reportId: number): Promise<Report> {
  return apiFetch<Report>(`/api/reports/${reportId}/`);
}

/** A flat array, not a paginated envelope — see the comments action in views.py. */
export function fetchComments(reportId: number): Promise<Comment[]> {
  return apiFetch<Comment[]>(`/api/reports/${reportId}/comments/`);
}

export function createComment(reportId: number, body: string): Promise<Comment> {
  return apiFetch<Comment>(`/api/reports/${reportId}/comments/`, {
    method: "POST",
    body: JSON.stringify({ body }),
  });
}

export function fetchReports(): Promise<Paginated<Report>> {
  return apiFetch<Paginated<Report>>("/api/reports/");
}

export function createReport(input: {
  title: string;
  description: string;
  type: Report["type"];
  visibility?: Report["visibility"];
  event_starts_at?: string;
  event_ends_at?: string;
  latitude: number;
  longitude: number;
}): Promise<Report> {
  return apiFetch<Report>("/api/reports/", { method: "POST", body: JSON.stringify(input) });
}

/** A separate request from createReport() — mixing JSON and multipart in one payload
 * complicates both, and the report needs to exist before an image can attach to it. */
export function uploadReportImage(reportId: number, file: File): Promise<ReportImage> {
  const body = new FormData();
  body.append("image", file);
  return apiFetch<ReportImage>(`/api/reports/${reportId}/images/`, { method: "POST", body });
}

export function updateReportStatus(reportId: number, status: Report["status"]): Promise<Report> {
  return apiFetch<Report>(`/api/reports/${reportId}/`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}
