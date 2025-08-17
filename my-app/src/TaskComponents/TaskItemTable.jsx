/* src/TaskComponents/TaskItemTable.jsx */
import StatusBadge from "./StatusBadge";

export default function TaskItemTable({ items }) {
  const cell = "px-2 py-1 text-gray-100 ";

  return (
    <div className="mt-3 overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="border-b border-zinc-700 text-zinc-400">
            <th className="px-2 py-1 text-center font-medium">ID</th>
            <th className="px-2 py-1 text-center font-medium">Status</th>
            <th className="px-2 py-1 text-center font-medium">Site-ID</th>
            <th className="px-2 py-1 text-center font-medium">Date</th>
            <th className="px-2 py-1 text-center font-medium">Tech</th>
          </tr>
        </thead>

        <tbody>
          {(items ?? [])
            .filter((it) => it && it.data)
            .map((it) => (
              <tr
                key={it.id}
                className="border-b border-zinc-700/60 last:border-0 hover:bg-zinc-700/20"
              >
                <td className={cell}>{it.id}</td>
                <td className={cell}>
                  <StatusBadge value={it.status} />
                </td>
                <td className={cell}>{it.data.site_id}</td>
                <td className={cell}>{it.data.date}</td>
                <td className={cell}>{it.data.tech}</td>
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  );
}
