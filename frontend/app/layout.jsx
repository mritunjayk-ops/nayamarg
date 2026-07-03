import "./globals.css";

export const metadata = {
  title: "NayaMarg",
  description: "AI career transition operating system for competitive exam aspirants.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
