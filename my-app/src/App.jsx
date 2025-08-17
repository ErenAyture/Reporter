import { useEffect, useState, useCallback } from "react";
import { API_BASE, fetchJSON } from "./api";
import { useWebSocket } from "./hooks/useWebSocket";

import NavBar from "./NavbarComponents/NavBar";
import Body from "./Body";
import ActiveTaskList from "./TaskComponents/ActiveTaskList";
import TaskCardList from "./TaskComponents/TaskCardList";
import CreateSsvTasksCard from "./TaskCreationComponents/CreateSsvTasksCard";

const USERNAME = "eren"; // ← adapt if you have auth

export default function App() {
  /* ───────────────────────────── state ───────────────────────────── */
  const [groups, setGroups] = useState([]); // all groups (cards)
  const [activeGroups, setActiveGroups] = useState([]); // QUEUED+RUNNING

  /* ────────────── helpers that mutate state immutably ───────────── */
  const mergeGroup = useCallback((partial) => {
    setGroups((prev) => {
      /* try to find existing */
      const idx = prev.findIndex((g) => g.id === partial.id);
      if (idx === -1) return [partial, ...prev]; // new card
      const next = [...prev];
      next[idx] = { ...next[idx], ...partial };
      return next;
    });
  }, []);

  const refreshAll = useCallback(async () => {
    const [all, act] = await Promise.all([
      fetchJSON(`/tasks/?username=${USERNAME}`),
      fetchJSON(`/tasks/active`),
    ]);
    setGroups(all);
    setActiveGroups(act);
  }, []);

  /* ───────────────────────── initial load ───────────────────────── */
  useEffect(() => {
    refreshAll().catch(console.error);
  }, [refreshAll]);

  /* ───────────────────────── web-socket ──────────────────────────── */
  useWebSocket(`${API_BASE.replace(/^http/, "ws")}/ws/user/${USERNAME}`, {
    onMessage: (msg) => {
      const { type, ...data } = msg;

      switch (type) {
        case "task_group_added":
          mergeGroup({
            id: data.group_id,
            status: data.status,
            items: (data.data ?? []).map((item) => ({
              id: item.id,
              status: item.status,
              data: {
                site_id: item.site_id,
                site_date: item.site_date,
                tech: item.tech,
              },
            })),
            created_at: new Date().toISOString(),
            type: "ssv",
          });
          break;

        case "task_group_status":
          mergeGroup({ id: data.group_id, status: data.status });

          setActiveGroups((prev) => {
            const stillActive = ["queued", "running"].includes(data.status);
            if (stillActive) {
              return prev.some((g) => g.id === data.group_id)
                ? prev.map((g) =>
                    g.id === data.group_id ? { ...g, status: data.status } : g
                  )
                : [...prev, { id: data.group_id, status: data.status }];
            }
            return prev.filter((g) => g.id !== data.group_id);
          });
          break;

        case "task_item_started":
          setGroups((prev) =>
            prev.map((g) => ({
              ...g,
              items: g.items?.map((it) =>
                it.id === data.item_id ? { ...it, status: data.status } : it
              ),
            }))
          );
          break;
        // case "task_item_started":
        //   setActiveGroups((groups) =>
        //     groups.map((group) => ({
        //       ...group,
        //       items: group.items.map((item) =>
        //         item.id === data.item_id
        //           ? { ...item, status: data.status }
        //           : item
        //       ),
        //     }))
        //   );
        //   break;

        case "task_item_finished":
          setGroups((prev) =>
            prev.map((g) => ({
              ...g,
              items: g.items?.map((it) =>
                it.id === data.item_id ? { ...it, status: data.status } : it
              ),
            }))
          );
          break;

        default:
          // console.log("Unhandled WS message:", msg);
          break;
      }
    },
  });
  /* ───────────────────────── web-socket task list ──────────────────────────── */
  useWebSocket(`${API_BASE.replace(/^http/, "ws")}/ws/broadcast`, {
    onMessage: (msg) => {
      const { type, ...data } = msg;

      switch (type) {
        case "task_group_status":
          setActiveGroups((prev) => {
            const stillActive = ["queued", "running"].includes(data.status);
            if (stillActive) {
              return prev.some((g) => g.id === data.group_id)
                ? prev.map((g) =>
                    g.id === data.group_id ? { ...g, status: data.status } : g
                  )
                : [...prev, { id: data.group_id, status: data.status }];
            }
            return prev.filter((g) => g.id !== data.group_id);
          });
          break;

        case "task_group_added":
          setActiveGroups((prev) => {
            if (!["queued", "running"].includes(data.status)) return prev;
            return prev.some((g) => g.id === data.group_id)
              ? prev
              : [{ id: data.group_id, status: data.status }, ...prev];
          });
          break;

        default:
          // console.log("Unhandled WS broadcast message:", msg);
          break;
      }
    },
  });

  /* ─────────────────────────── render ───────────────────────────── */
  return (
    <>
      <NavBar username={USERNAME} />
      <Body>
        <CreateSsvTasksCard username={USERNAME} />
        <ActiveTaskList groups={activeGroups} />
        <TaskCardList groups={groups} />
      </Body>
    </>
  );
}
