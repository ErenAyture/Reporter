/* simple fetch wrappers used by TaskCardList */
export const API = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

export async function apiDelete(path) {
  const res = await fetch(`${API}${path}`, { method: "DELETE" });
  if (!res.ok) throw new Error(res.statusText);
}

export async function apiDownload(path, filename) {
  const res = await fetch(`${API}${path}`);
  if (!res.ok) throw new Error(res.statusText);

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
