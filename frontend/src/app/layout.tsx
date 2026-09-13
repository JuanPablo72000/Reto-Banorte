import type { Metadata, Viewport } from "next";
import { A11yProvider } from "@/components/accessibility/A11yProvider";
import { AuthProvider } from "@/components/auth/AuthProvider";
import "./globals.css";

export const metadata: Metadata = {
    title: "Banca Personal Adaptativa",
    description: "Demo académica de banca personal con interfaz adaptativa",
};

export const viewport: Viewport = {
    width: "device-width",
    initialScale: 1,
    viewportFit: "cover",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="es" suppressHydrationWarning>
            <body>
                <A11yProvider>
                    <AuthProvider>{children}</AuthProvider>
                </A11yProvider>
            </body>
        </html>
    );
}
