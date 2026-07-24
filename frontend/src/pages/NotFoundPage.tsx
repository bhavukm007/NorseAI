import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <section className="page">
      <p className="eyebrow">404</p>
      <h1>Page not found</h1>
      <p className="page-description">The requested workspace route does not exist.</p>
      <Link className="text-link" to="/dashboard">
        Return to overview
      </Link>
    </section>
  );
}
