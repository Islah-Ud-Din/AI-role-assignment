import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SEO Article Generator",
  description: "AI-powered SEO content generation platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
