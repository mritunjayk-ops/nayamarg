import Link from "next/link";

export default function NotFound() {
  return (
    <main className="not-found-page">
      <section className="panel not-found-card">
        <p className="eyebrow">NayaMarg</p>
        <h1>Page not found</h1>
        <p>The page you requested does not exist.</p>
        <Link href="/">Return to dashboard</Link>
      </section>
    </main>
  );
}
