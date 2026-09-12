import type { Metadata } from "next";
import { A11yProvider } from "@/components/accessibility/A11yProvider";
import "./globals.css";

export const metadata: Metadata = {
    title: "Banca Personal Adaptativa",
    description: "Demo académica de banca personal con interfaz adaptativa",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="es">
        <body>
        <A11yProvider>{children}</A11yProvider>
        </body>
        </html>
    );
}