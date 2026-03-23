import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Be Better",
  description: "找到你的天賦方向，成為更好的自己",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-Hant">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin=""
        />
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Outfit:wght@600;700;800&display=swap"
        />
      </head>
      <body className="bg-brand-bg">{children}</body>
    </html>
  );
}
