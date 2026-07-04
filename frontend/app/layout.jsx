import { Spectral, Hanken_Grotesk } from "next/font/google";
import "./globals.css";

const display = Spectral({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  style: ["normal", "italic"],
  variable: "--font-display",
  display: "swap",
});

const body = Hanken_Grotesk({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-body",
  display: "swap",
});

export const metadata = {
  title: "NayaMarg — Find your new path",
  description:
    "A calm, personalized career transition companion for UPSC and competitive-exam aspirants charting a realistic next chapter.",
  icons: { icon: "/nayamarg_logo.svg" },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable}`}>
      <body>{children}</body>
    </html>
  );
}
