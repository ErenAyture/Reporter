import TaskCard from "./TaskCard";
import { API_BASE } from "../api";

export default function TaskCardList({ groups }) {
  const handleDownload = async (groupId) => {
    try {
      const res = await fetch(`${API_BASE}/download/${groupId}`);
      if (!res.ok) throw new Error("Failed to fetch file.");

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `ssv_group_${groupId}.zip`; // or .xlsx etc.
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert(`Download failed: ${err.message}`);
    }
  };
  return (
    <section className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {groups.map((g) => (
        <TaskCard key={g.id} group={g} onDownload={handleDownload} />
      ))}
    </section>
  );
}
