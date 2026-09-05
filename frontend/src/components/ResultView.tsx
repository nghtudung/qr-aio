import { Copy, Download, ExternalLink } from "lucide-react";
import { ScanResponse } from "../lib/api";

export function ResultView({ result }: { result: ScanResponse | null }) {
  if (!result) return null;
  if (!result.found)
    return (
      <div className="rounded-md border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
        No QR code was found.
      </div>
    );
  const first = result.results[0];
  const download = () => {
    const blob = new Blob([first.raw], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "qr-result.txt";
    link.click();
    URL.revokeObjectURL(url);
  };
  return (
    <div className="space-y-4 rounded-md border border-line bg-white p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="label">Detected {first.content_type}</p>
          <p className="break-all text-sm text-slate-700">{first.raw}</p>
        </div>
        <div className="flex gap-2">
          {first.content_type === "url" && (
            <a
              className="rounded-md border border-line p-2"
              href={String(first.parsed.url)}
              target="_blank"
              rel="noreferrer"
              title="Open link"
            >
              <ExternalLink size={17} />
            </a>
          )}
          <button
            className="rounded-md border border-line p-2"
            onClick={() => navigator.clipboard.writeText(first.raw)}
            title="Copy result"
          >
            <Copy size={17} />
          </button>
          <button
            className="rounded-md border border-line p-2"
            onClick={download}
            title="Download result"
          >
            <Download size={17} />
          </button>
        </div>
      </div>
      {Object.keys(first.parsed).length > 0 && (
        <pre className="overflow-auto rounded-md bg-slate-50 p-3 text-xs text-slate-700">
          {JSON.stringify(first.parsed, null, 2)}
        </pre>
      )}
    </div>
  );
}
