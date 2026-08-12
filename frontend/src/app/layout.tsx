import type { Metadata } from "next";
import "./globals.css";

import { UserProvider } from "@/lib/auth";

export const metadata: Metadata = {
  title: "MapApp",
  description: "Haritada sivil sorunlar ve talepler",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr">
      <body>
        {/* Wraps the whole app so the header and every page share one auth state. */}
        <UserProvider>{children}</UserProvider>
      </body>
    </html>
  );
}
