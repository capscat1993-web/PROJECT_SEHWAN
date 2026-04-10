export function DashboardShell({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className="page-shell">
      <div className="background-orb background-orb-a" />
      <div className="background-orb background-orb-b" />
      <main className="page-content">{children}</main>
    </div>
  );
}
