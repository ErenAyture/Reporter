/* src/TaskComponents/StatusBadge.jsx */
export default function StatusBadge({ value }) {
  const palette = {
    queued: "bg-yellow-500/20 text-yellow-400",
    running: "bg-blue-500/20  text-blue-400",
    ok: "bg-emerald-500/20 text-emerald-400",
    done: "bg-emerald-500/20 text-emerald-400",
    error: "bg-red-500/20   text-red-400",
  };
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ${
        palette[value] ?? "bg-zinc-700/20"
      }`}
    >
      {value}
    </span>
  );
}
