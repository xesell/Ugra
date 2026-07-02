import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { StatusBar } from "./StatusBar";

export function AppLayout() {
  return (
    <div className="flex h-full min-w-app flex-col">
      <div className="flex min-h-0 flex-1">
        <Sidebar />
        <main className="flex min-w-0 flex-1 flex-col overflow-hidden">
          <div className="flex-1 overflow-auto p-8">
            <Outlet />
          </div>
        </main>
      </div>
      <StatusBar />
    </div>
  );
}
