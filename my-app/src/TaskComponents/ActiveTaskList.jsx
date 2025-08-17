import StatusBadge from "./StatusBadge";

export default function ActiveTaskList({ groups }) {
  if (!groups.length) return null;

  return (
    <section className="mt-6 rounded-lg bg-zinc-800 p-4">
      <h3 className="mb-2 text-sm font-semibold text-gray-100">
        Active task-groups
      </h3>

      <div className="max-h-48 overflow-y-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-700 text-zinc-400">
              <th className="px-2 py-1 text-center font-medium">ID</th>
              <th className="px-2 py-1 text-center font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {groups.map((g) => (
              <tr
                key={g.id}
                className="border-b border-zinc-700/60 last:border-0"
              >
                <td className="px-2 py-1">{g.id}</td>
                <td className="px-2 py-1">
                  <StatusBadge value={g.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
