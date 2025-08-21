import { useEffect, useState, useCallback, useMemo } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { API_BASE, fetchJSON } from "./api";
import { useWebSocket } from "./hooks/useWebSocket";

import NavBar from "./NavbarComponents/NavBar";
import Body from "./Body";
import ActiveTaskList from "./TaskComponents/ActiveTaskList";
import TaskCardList from "./TaskComponents/TaskCardList";
import CreateSsvTasksCard from "./TaskCreationComponents/CreateSsvTasksCard";

// ------- client-expiry helpers (15 min or earlier if JWT.exp) -------
const EXP_COOKIE = "rpt_front_exp";
function setExpiryCookie(unixMs) {
  const d = new Date(unixMs);
  document.cookie = `${EXP_COOKIE}=${encodeURIComponent(
    unixMs
  )}; expires=${d.toUTCString()}; path=/; SameSite=Lax`;
}
function readExpiryCookie() {
  const m = document.cookie.match(new RegExp(`(?:^|; )${EXP_COOKIE}=([^;]*)`));
  return m ? parseInt(decodeURIComponent(m[1])) : null;
}
function clearExpiryCookie() {
  document.cookie = `${EXP_COOKIE}=; Max-Age=0; path=/`;
}

// --------- Router-based auth: read ?t=, verify, then clean URL ---------
function useAuthFromRouter() {
  const [username, setUsername] = useState(null);
  const [ready, setReady] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const now = Date.now();
    // 1) query param ?t=...
    const params = new URLSearchParams(location.search);
    let token = params.get("t");

    // 2) path forms: /t=<token> or /token/<token>
    if (!token) {
      const path = decodeURIComponent(location.pathname);
      const m =
        path.match(/^\/t=(.+)$/) || // /t=<token>
        path.match(/^\/token\/(.+)$/); // /token/<token>
      if (m) token = m[1];
    }

    (async () => {
      if (token) {
        try {
          const res = await fetch(`${API_BASE}/auth/verify`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token }),
          });
          if (!res.ok) throw new Error("verify failed");
          const data = await res.json(); // { ok, username, exp }

          sessionStorage.setItem("rpt_user", data.username);
          setUsername(data.username);

          const jwtMs = data.exp ? data.exp * 1000 : Infinity;
          const fifteen = now + 15 * 60 * 1000;
          setExpiryCookie(Math.min(jwtMs, fifteen));
        } catch {
          sessionStorage.removeItem("rpt_user");
          clearExpiryCookie();
          setUsername(null);
        } finally {
          // Clean the URL (remove ?t=...) without adding history
          navigate("/", { replace: true });
          setReady(true);
        }
      } else {
        // refresh path: enforce client-side expiry
        const expTs = readExpiryCookie();
        if (expTs && expTs > now) {
          const saved = sessionStorage.getItem("rpt_user");
          if (saved) setUsername(saved);
        } else {
          sessionStorage.removeItem("rpt_user");
          clearExpiryCookie();
          setUsername(null);
        }
        setReady(true);
      }
    })();
  }, [location.search, location.pathname, navigate]);

  return { username, ready };
}

export default function App() {
  const { username, ready } = useAuthFromRouter();

  /* ───────────────────────────── state ───────────────────────────── */
  const [groups, setGroups] = useState([]); // all groups (cards)
  const [activeGroups, setActiveGroups] = useState([]); // QUEUED+RUNNING

  /* ────────────── helpers that mutate state immutably ───────────── */
  const mergeGroup = useCallback((partial) => {
    setGroups((prev) => {
      const idx = prev.findIndex((g) => g.id === partial.id);
      if (idx === -1) return [partial, ...prev];
      const next = [...prev];
      next[idx] = { ...next[idx], ...partial };
      return next;
    });
  }, []);

  const refreshAll = useCallback(async (u) => {
    const [all, act] = await Promise.all([
      fetchJSON(`/tasks/?username=${encodeURIComponent(u)}`),
      fetchJSON(`/tasks/active`),
    ]);
    setGroups(all);
    setActiveGroups(act);
  }, []);

  /* ───────────────────────── initial load ───────────────────────── */
  useEffect(() => {
    if (!username) return;
    refreshAll(username).catch(console.error);
  }, [refreshAll, username]);

  /* ───────────────────────── web-socket (USER) ───────────────────── */
  const userWsUrl = useMemo(
    () =>
      username
        ? `${API_BASE.replace(/^http/, "ws")}/ws/user/${encodeURIComponent(
            username
          )}`
        : null,
    [username]
  );

  useWebSocket(userWsUrl, {
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
          break;
      }
    },
  });

  /* ───────────────────────── web-socket (BROADCAST) ───────────────── */
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
          break;
      }
    },
  });

  /* ─────────────────────────── render ───────────────────────────── */
  if (!ready) return null;
  if (!username)
    return (
      <div className="p-6 text-gray-200">
        Session expired or not authenticated.
      </div>
    );

  return (
    <>
      <NavBar username={username} />
      <Body>
        <CreateSsvTasksCard username={username} />
        <ActiveTaskList groups={activeGroups} />
        <TaskCardList groups={groups} />
      </Body>
    </>
  );
}
