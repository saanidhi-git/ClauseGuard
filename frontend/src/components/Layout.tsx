import { useEffect, useState } from "react";
import { NavLink, Outlet, Link, useLocation } from "react-router-dom";
import { FileSearch, History, BarChart3, Info, Moon, Sun, Menu, X, ShieldCheck } from "lucide-react";

const NAV = [
  { to: "/", label: "Analyze", icon: FileSearch },
  { to: "/history", label: "History", icon: History },
  { to: "/insights", label: "Model Insights", icon: BarChart3 },
  { to: "/about", label: "About", icon: Info },
];

function useTheme() {
  const [dark, setDark] = useState(() => document.documentElement.classList.contains("dark"));
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    try {
      localStorage.setItem("cg-theme", dark ? "dark" : "light");
    } catch {
      /* storage blocked */
    }
  }, [dark]);
  return [dark, setDark] as const;
}

export default function Layout() {
  const [dark, setDark] = useTheme();
  const [open, setOpen] = useState(false);
  const { pathname } = useLocation();

  // start each page at the top
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  const link = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition ${
      isActive
        ? "bg-accent-50 text-accent-700 dark:bg-accent-600/15 dark:text-accent-100"
        : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
    }`;

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/85 backdrop-blur dark:border-slate-800 dark:bg-slate-950/85">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4">
          <Link to="/" className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-accent-600 text-white">
              <ShieldCheck className="h-5 w-5" aria-hidden />
            </span>
            <span className="leading-tight">
              <span className="block text-lg">ClauseGuard</span>
              <span className="hidden text-xs font-normal text-slate-500 sm:block">Know what you sign</span>
            </span>
          </Link>
          <nav className="hidden items-center gap-1 md:flex" aria-label="Main">
            {NAV.map((n) => (
              <NavLink key={n.to} to={n.to} end={n.to === "/"} className={link}>
                <n.icon className="h-4 w-4" aria-hidden />
                {n.label}
              </NavLink>
            ))}
          </nav>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setDark(!dark)}
              className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
              aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
            >
              {dark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </button>
            <button
              className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 md:hidden dark:text-slate-300 dark:hover:bg-slate-800"
              onClick={() => setOpen(!open)}
              aria-label="Menu"
              aria-expanded={open}
            >
              {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>
        {open && (
          <nav className="border-t border-slate-200 px-4 py-2 md:hidden dark:border-slate-800" aria-label="Mobile">
            {NAV.map((n) => (
              <NavLink key={n.to} to={n.to} end={n.to === "/"} className={link} onClick={() => setOpen(false)}>
                <n.icon className="h-4 w-4" aria-hidden />
                {n.label}
              </NavLink>
            ))}
          </nav>
        )}
      </header>

      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
}
