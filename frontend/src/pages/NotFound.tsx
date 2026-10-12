import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-xl px-4 py-24 text-center">
      <p className="text-5xl font-bold text-accent-600">404</p>
      <h1 className="mt-3 text-xl font-semibold text-slate-900 dark:text-white">Page not found</h1>
      <Link to="/" className="btn-primary mt-6">Go to ClauseGuard</Link>
    </div>
  );
}
