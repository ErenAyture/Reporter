import { useState } from "react";
import { ChevronDown, ChevronUp, Download, Trash2 } from "lucide-react";
import StatusBadge from "./StatusBadge";
import TaskItemTable from "./TaskItemTable";

/* ----------------------------------------------------------------------- */
export default function TaskCard({ group, onDelete, onDownload }) {
  const [open, setOpen] = useState(false);

  /* which buttons to show ------------------------------------------------- */
  const canDownload = group.status === "done";
  const canDelete = group.status !== "running";

  return (
    <article
      className={`rounded-xl bg-zinc-800 shadow-sm p-5 transition-all
                  ${open ? "sm:col-span-2 lg:col-span-3" : ""}`}
    >
      {/* header ------------------------------------------------------------ */}
      <header className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-100">
            Task&nbsp;Group #{group.id}
          </h2>
          <time className="text-xs text-gray-400">
            {new Date(group.created_at).toLocaleString()}
          </time>
        </div>

        {/* type + status badges */}
        <div className="flex items-center gap-2">
          <StatusBadge value={group.type} />
          <StatusBadge value={group.status} />
        </div>
      </header>

      {/* toggle row + icon buttons ---------------------------------------- */}
      <div className="mt-4 flex items-center gap-3">
        <button
          onClick={() => setOpen((o) => !o)}
          className="flex items-center gap-1 text-sm text-gray-300 hover:text-white"
        >
          {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          {open ? "Hide items" : "Show items"}
        </button>

        {/* right-aligned buttons */}
        <div className="ml-auto flex items-center gap-2">
          {canDownload && (
            <button
              title="Download archive"
              className="p-1 rounded hover:bg-zinc-700"
              onClick={() => onDownload?.(group.id)}
            >
              <Download size={18} className="text-gray-300 hover:text-white" />
            </button>
          )}
          {canDelete && (
            <button
              title="Delete task group"
              className="p-1 rounded hover:bg-zinc-700"
              onClick={() => onDelete?.(group.id)}
            >
              <Trash2 size={18} className="text-red-400 hover:text-red-500" />
            </button>
          )}
        </div>
      </div>

      {/* collapsible content ---------------------------------------------- */}
      {open && (
        <div className="mt-4">
          <TaskItemTable items={group.items} />
        </div>
      )}
    </article>
  );
}
