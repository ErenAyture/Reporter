/* ──────────────────────────────────────────
   src/NavbarComponents/NavBar.jsx
   ────────────────────────────────────────── */
import { User2 } from "lucide-react";
import { useEffect, useState } from "react";
/**
 * Simple gradient navbar that greets the user.
 *
 * Props
 *  - username   string   name to greet (required)
 */
export default function NavBar({ username = "Guest" }) {
  const [leftMs, setLeftMs] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      const m = document.cookie.match(/(?:^|; )rpt_front_exp=([^;]*)/);
      const exp = m ? parseInt(decodeURIComponent(m[1])) : 0;
      setLeftMs(Math.max(0, exp - Date.now()));
    }, 1000);
    return () => clearInterval(id);
  }, []);

  const mm = String(Math.floor(leftMs / 60000)).padStart(2, "0");
  const ss = String(Math.floor((leftMs % 60000) / 1000)).padStart(2, "0");
  return (
    <nav
      className="sticky top-0 z-40 h-14 w-full select-none border-b
                 border-zinc-700/50 bg-gradient-to-r from-zinc-900 to-fuchsia-700
                 px-4 shadow-md backdrop-blur lg:px-8"
    >
      <div className="mx-auto flex h-full max-w-7xl items-center justify-between">
        {/* left – logo / title */}
        <div className="flex items-center gap-2 text-sm font-semibold tracking-wide text-gray-100">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            className="h-6 w-6 text-indigo-400"
          >
            <path d="M12 2 2 7l10 5 10-5-10-5Zm0 7L2 7v10l10 5 10-5V7l-10 2Z" />
          </svg>
          Task Reporter
        </div>

        {/* right – greeting */}
        <div className="flex items-center gap-2 text-sm text-gray-200">
          {leftMs > 0 && (
            <div className="text-xs opacity-70">
              Session: {mm}:{ss}
            </div>
          )}
          <User2 size={18} className="text-indigo-300" />
          <span className="hidden sm:inline">Welcome,&nbsp;</span>
          <span className="font-medium">{username}</span>
        </div>
      </div>
    </nav>
  );
}
