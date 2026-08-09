import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MapApp",
  description: "Civic issues and requests on a map",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
