export function DashboardShell({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className="page-shell">
      <main className="page-content">{children}</main>
    </div>
  );
}
