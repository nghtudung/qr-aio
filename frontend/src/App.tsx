import { QrCode, ScanLine } from "lucide-react";
import { GeneratorPage } from "./pages/GeneratorPage";
import { ScannerPage } from "./pages/ScannerPage";
import { useState } from "react";

type Page = "generate" | "scan";

export function App() {
  const [page, setPage] = useState<Page>("generate");
  return (
    <div className="min-h-screen bg-mist">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-md bg-ink text-white">
              <QrCode size={22} />
            </div>
            <div>
              <h1 className="text-xl font-semibold">QR AIO</h1>
              <p className="text-sm text-slate-500">
                Generate, export, and scan QR codes
              </p>
            </div>
          </div>
          <nav className="flex rounded-md border border-line bg-slate-50 p-1">
            <button
              className={`flex items-center gap-2 rounded px-3 py-2 text-sm ${page === "generate" ? "bg-white shadow-sm" : "text-slate-600"}`}
              onClick={() => setPage("generate")}
            >
              <QrCode size={16} /> Generate
            </button>
            <button
              className={`flex items-center gap-2 rounded px-3 py-2 text-sm ${page === "scan" ? "bg-white shadow-sm" : "text-slate-600"}`}
              onClick={() => setPage("scan")}
            >
              <ScanLine size={16} /> Scan
            </button>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">
        {page === "generate" ? <GeneratorPage /> : <ScannerPage />}
      </main>
    </div>
  );
}
