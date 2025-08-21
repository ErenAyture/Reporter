// /* eslint-disable react-hooks/rules-of-hooks */
// import { useEffect, useRef } from "react";

// export function useWebSocket(url, { onMessage }) {
//   const wsRef = useRef();

//   useEffect(() => {
//     let alive = true;

//     function connect() {
//       if (!alive) return;

//       const ws = new WebSocket(url);
//       wsRef.current = ws;

//       ws.addEventListener("close", (e) => {
//         const code = e.code;
//         const reason = e.reason || "No reason";
//         console.log(`WebSocket closed: [${code}] ${reason}`);
//       });

//       ws.onmessage = (ev) => {
//         try {
//           const msg = JSON.parse(ev.data);
//           onMessage?.(msg);
//           console.log(msg);
//         } catch (err) {
//           console.warn("Invalid WebSocket message", ev.data);
//           console.log(err);
//         }
//       };

//       ws.onclose = () => {
//         /* auto-reconnect after 2s */
//         if (alive) setTimeout(connect, 2000);
//       };
//     }

//     connect();

//     return () => {
//       alive = false;
//       wsRef.current?.close();
//     };
//   }, [url, onMessage]);
//   useEffect(() => {
//     const handleUnload = () => {
//       wsRef.current?.close();
//     };
//     window.addEventListener("beforeunload", handleUnload);
//     return () => window.removeEventListener("beforeunload", handleUnload);
//   }, []);
// }
/* eslint-disable react-hooks/rules-of-hooks */
import { useEffect, useRef } from "react";

export function useWebSocket(url, { onMessage }) {
  const wsRef = useRef(null);

  useEffect(() => {
    if (!url) return; // ← guard: don't connect until we have a URL
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("✅ WebSocket connected");
    };

    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        console.log("📨 WebSocket message:", msg);
        onMessage?.(msg);
      } catch (err) {
        console.warn("Invalid WebSocket message", ev.data);
      }
    };

    ws.onerror = (err) => {
      console.error("🔥 WebSocket error:", err);
    };

    ws.onclose = (e) => {
      console.log(
        `⚠️ WebSocket closed [${e.code}]: ${e.reason || "No reason"}`
      );
    };

    const handleUnload = () => {
      wsRef.current?.close(1000, "Client closed");
    };
    window.addEventListener("beforeunload", handleUnload);

    return () => {
      window.removeEventListener("beforeunload", handleUnload);
      wsRef.current?.close(1000, "React cleanup");
    };
  }, [url, onMessage]);
}
