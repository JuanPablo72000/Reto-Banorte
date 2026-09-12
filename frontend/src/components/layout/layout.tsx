import type { Metadata } from "next";
import "./globals.css";
import { A11yProvider } from "@/components/accessibility/A11yProvider";
import { AppShell } from "@/components/layout/AppShell";

export const metadata: Metadata = {
    title: "Banca Personal Adaptativa",
    description: "Demo académica de banca personal con interfaz adaptativa e IA",
};

export default function RootLayout({
                                       children,
                                   }: {
    children: React.ReactNode;
}) {
    return (
        <html lang="es">
        <body>
        <A11yProvider>
            <AppShell>{children}</AppShell>
        </A11yProvider>
        </body>
        </html>
    );
}