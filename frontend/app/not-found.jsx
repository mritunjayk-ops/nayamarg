import Link from "next/link";

export default function NotFound() {
  return (
    <main className="center-screen">
      <div>
        <span className="section-kicker">NayaMarg</span>
        <h1>This path leads nowhere</h1>
        <p>The page you were looking for doesn&apos;t exist.</p>
        <Link href="/">← Back to start</Link>
      </div>
    </main>
  );
}
