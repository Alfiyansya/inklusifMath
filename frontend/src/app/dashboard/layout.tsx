import { Header } from "@/components/layout/Header";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Header userName="asd" userRole="Guru" userInitial="A" />
      <main id="main-content">{children}</main>
    </>
  );
}
