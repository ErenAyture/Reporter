/* ------------------------------------------------------------------
   src/TaskCreationComponents/CreateSsvTasksCard.jsx
-------------------------------------------------------------------*/
import { useState, useEffect, useRef } from "react";
import { Plus, Trash2, Calendar, ChevronDown, ChevronUp } from "lucide-react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";

/* ─────────────────────────── helpers ─────────────────────────── */
const TECHS = ["LTE", "NR", "UMTS", "GSM"];

const todayMinus2 = () => {
  const d = new Date();
  d.setDate(d.getDate() - 2);
  d.setHours(0, 0, 0, 0);
  return d;
};

// local “YYYY-MM-DD” (no TZ shift)
const fmtDate = (d) => d.toLocaleDateString("sv-SE");

/* ─────────────────────────── config ──────────────────────────── */
const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

/* ───────────────────────── component ─────────────────────────── */
export default function CreateSsvTasksCard({ username }) {
  const [open, setOpen] = useState(false);

  /* ---------- autocomplete ---------- */
  const [query, setQuery] = useState("");
  const [matches, setMatches] = useState([]);
  const abortRef = useRef();

  /* ---------- rows ---------- */
  const [rows, setRows] = useState([]);

  const addSite = (site_id) => {
    if (rows.length >= 10 || rows.some((r) => r.site_id === site_id)) return;
    setRows((p) => [...p, { site_id, date: todayMinus2(), tech: "LTE" }]); // ← fixed
    setQuery("");
    setMatches([]);
  };

  const updateRow = (i, patch) =>
    setRows((r) =>
      r.map((row, idx) => (idx === i ? { ...row, ...patch } : row))
    );

  const removeRow = (i) => setRows((r) => r.filter((_, idx) => idx !== i));
  const clearAllRows = () => setRows([]);

  /* ---------- autocomplete → API ---------- */
  useEffect(() => {
    const q = query.trim();
    if (!q) {
      setMatches([]);
      abortRef.current?.abort();
      return;
    }

    const t = setTimeout(() => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      fetch(`${API_BASE}/ssv/sites/by_prefix/${encodeURIComponent(q)}`, {
        signal: controller.signal,
      })
        .then((r) => (r.ok ? r.json() : Promise.reject()))
        .then(setMatches)
        .catch(() => !controller.signal.aborted && setMatches([]));
    }, 250);

    return () => clearTimeout(t);
  }, [query]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [statusMessage, setStatusMessage] = useState(""); // success/failure
  const statusTimeout = useRef();
  /* ---------- POST /ssv_task/run ---------- */
  const handleCreate = async () => {
    if (!rows.length) return;

    const payload = {
      username,
      sites: rows.map(({ site_id, date, tech }) => ({
        site_id: String(site_id),
        date: fmtDate(date),
        tech,
      })),
    };

    setIsSubmitting(true);
    setStatusMessage(""); // reset

    try {
      const res = await fetch(`${API_BASE}/ssv_task/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error(await res.text());

      setStatusMessage("✔ Tasks successfully queued.");
      clearAllRows();

      // Delay card closing to show status message
      statusTimeout.current = setTimeout(() => {
        setStatusMessage("");
        setOpen(false);
      }, 5000); // wait 5 seconds before collapsing
    } catch (err) {
      setStatusMessage(`✖ Failed to queue tasks: ${err.message}`);
      statusTimeout.current = setTimeout(() => setStatusMessage(""), 5000);
    } finally {
      setIsSubmitting(false);
    }
  };

  /* ---------- UI ---------- */
  return (
    <>
      <article
        className="rounded-xl p-5 shadow-sm
                        bg-gradient-to-tr from-zinc-900 via-zinc-800 to-pink-600/70"
      >
        {/* header */}
        <header
          className="flex cursor-pointer select-none items-center justify-between"
          onClick={() => setOpen((o) => !o)}
        >
          <h2 className="text-lg font-semibold text-gray-100">
            Create SSV Tasks
          </h2>
          {open ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </header>

        {open && (
          <div className="mt-4 space-y-4">
            {/* search */}
            <div className="relative">
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={
                  rows.length >= 10
                    ? "Maximum 10 site seçildi"
                    : "Search Site ID…"
                }
                disabled={rows.length >= 10}
                className="w-full rounded-md bg-zinc-700/60 px-3 py-2 text-sm
                         text-gray-100 placeholder:text-zinc-400
                         disabled:opacity-40 focus:outline-none"
              />

              {matches.length > 0 && (
                <ul
                  className="absolute z-20 mt-1 w-full max-h-48 overflow-y-auto
                           rounded-md bg-zinc-800/95 text-sm text-gray-100
                           ring-1 ring-zinc-600/50 backdrop-blur"
                >
                  {matches.map((id) => (
                    <li
                      key={id}
                      onClick={() => addSite(id)}
                      className="cursor-pointer px-3 py-1 hover:bg-zinc-600/60"
                    >
                      {id}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* table */}
            {rows.length > 0 && (
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b border-zinc-700 text-zinc-400">
                      <th className="px-2 py-1 text-center font-medium">
                        Site&nbsp;ID
                      </th>
                      <th className="px-2 py-1 text-center font-medium">
                        Date
                      </th>
                      <th className="px-2 py-1 text-center font-medium">
                        Tech
                      </th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row, idx) => (
                      <tr
                        key={row.site_id}
                        className="border-b border-zinc-700/60 last:border-0"
                      >
                        <td className="px-2 py-1 text-center font-semibold">
                          {row.site_id}
                        </td>

                        {/* datepicker */}
                        <td className="px-2 py-1 text-center">
                          <DatePicker
                            selected={row.date}
                            onChange={(d) => updateRow(idx, { date: d })}
                            dateFormat="yyyy-MM-dd"
                            popperClassName="z-50"
                            customInput={
                              <button
                                type="button"
                                className="inline-flex w-32 items-center justify-center gap-1
                                         rounded bg-zinc-700/60 px-2 py-1"
                              >
                                <Calendar size={14} />
                                {fmtDate(row.date)}
                              </button>
                            }
                          />
                        </td>

                        {/* tech */}
                        <td className="px-2 py-1 text-center">
                          <select
                            value={row.tech}
                            onChange={(e) =>
                              updateRow(idx, { tech: e.target.value })
                            }
                            className="rounded bg-zinc-700/60 px-2 py-1 text-center"
                          >
                            {TECHS.map((t) => (
                              <option key={t}>{t}</option>
                            ))}
                          </select>
                        </td>

                        {/* delete row */}
                        <td className="px-2 py-1 text-center">
                          <button
                            onClick={() => removeRow(idx)}
                            className="text-red-400 hover:text-red-500"
                          >
                            <Trash2 size={16} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* footer buttons */}
            <div className="flex items-center gap-2">
              <button
                onClick={handleCreate}
                disabled={rows.length === 0 || !username}
                className="inline-flex items-center gap-1 rounded-md bg-indigo-600
                         px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
              >
                <Plus size={16} /> Add&nbsp;Task
              </button>
              <button
                onClick={clearAllRows}
                disabled={rows.length === 0}
                className="inline-flex items-center gap-1 rounded-md bg-zinc-600
                         px-4 py-2 text-sm font-medium text-gray-100 disabled:opacity-40"
              >
                <Trash2 size={16} /> Clear
              </button>
            </div>
          </div>
        )}
      </article>
      <div className="mt-4 flex items-center space-x-2 min-h-[1.5rem]">
        {isSubmitting && (
          <>
            <div className="animate-spin h-4 w-4 border-t-2 border-white rounded-full"></div>
            <div className="text-sm text-zinc-300">Submitting tasks…</div>
          </>
        )}

        {!isSubmitting && statusMessage && (
          <div className="text-sm text-white">{statusMessage}</div>
        )}
      </div>
    </>
  );
}
