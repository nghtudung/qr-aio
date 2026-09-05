import { Camera, Link, Upload } from "lucide-react";
import type { ReactNode } from "react";
import { useEffect, useRef, useState } from "react";
import { Html5Qrcode } from "html5-qrcode";
import { ResultView } from "../components/ResultView";
import { ScanResponse, scanUpload, scanUrl } from "../lib/api";

type Tab = "camera" | "upload" | "url";

export function ScannerPage() {
  const [tab, setTab] = useState<Tab>("camera");
  const [result, setResult] = useState<ScanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [url, setUrl] = useState("");
  const [cameraFacing, setCameraFacing] = useState<"environment" | "user">(
    "environment",
  );
  const scanner = useRef<Html5Qrcode | null>(null);

  useEffect(() => {
    if (tab !== "camera") return;
    const id = "qr-camera-reader";
    const instance = new Html5Qrcode(id);
    scanner.current = instance;
    instance
      .start(
        { facingMode: cameraFacing },
        { fps: 8, qrbox: { width: 260, height: 260 } },
        (decodedText) =>
          setResult({
            found: true,
            results: [
              {
                raw: decodedText,
                content_type: classifyLocal(decodedText),
                parsed: {},
              },
            ],
            warnings: [],
          }),
        () => undefined,
      )
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Camera unavailable"),
      );
    return () => {
      void instance
        .stop()
        .catch(() => undefined)
        .then(() => instance.clear());
      scanner.current = null;
    };
  }, [tab, cameraFacing]);

  async function upload(file: File) {
    setError(null);
    try {
      setResult(await scanUpload(file));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to scan image");
    }
  }

  async function scanRemote() {
    setError(null);
    try {
      setResult(await scanUrl(url));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to scan URL");
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_420px]">
      <section className="panel rounded-md p-4">
        <div className="mb-4 flex rounded-md border border-line bg-slate-50 p-1">
          <TabButton
            active={tab === "camera"}
            onClick={() => setTab("camera")}
            icon={<Camera size={16} />}
            label="Camera"
          />
          <TabButton
            active={tab === "upload"}
            onClick={() => setTab("upload")}
            icon={<Upload size={16} />}
            label="Upload"
          />
          <TabButton
            active={tab === "url"}
            onClick={() => setTab("url")}
            icon={<Link size={16} />}
            label="Image URL"
          />
        </div>
        {tab === "camera" && (
          <div className="space-y-4">
            <div
              id="qr-camera-reader"
              className="min-h-[360px] overflow-hidden rounded-md border border-line bg-slate-950"
            />
            <button
              className="rounded-md border border-line bg-white px-3 py-2 text-sm"
              onClick={() =>
                setCameraFacing((value) =>
                  value === "environment" ? "user" : "environment",
                )
              }
            >
              Switch camera
            </button>
          </div>
        )}
        {tab === "upload" && (
          <label
            className="grid min-h-[360px] cursor-pointer place-items-center rounded-md border border-dashed border-line bg-white p-8 text-center"
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => {
              event.preventDefault();
              const file = event.dataTransfer.files[0];
              if (file) void upload(file);
            }}
          >
            <div>
              <Upload className="mx-auto mb-3 text-slate-500" size={34} />
              <p className="font-medium">Drop an image or select a file</p>
              <p className="text-sm text-slate-500">PNG, JPG, JPEG, or WEBP</p>
            </div>
            <input
              className="hidden"
              type="file"
              accept="image/png,image/jpeg,image/webp"
              onChange={(event) =>
                event.target.files?.[0] && void upload(event.target.files[0])
              }
            />
          </label>
        )}
        {tab === "url" && (
          <div className="space-y-3 rounded-md border border-line bg-white p-4">
            <label className="space-y-1.5">
              <span className="label">Image URL</span>
              <input
                className="control"
                value={url}
                onChange={(event) => setUrl(event.target.value)}
                placeholder="https://example.com/image.png"
              />
            </label>
            <button
              className="rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white"
              onClick={() => void scanRemote()}
            >
              Scan URL
            </button>
          </div>
        )}
        {error && (
          <p className="mt-4 rounded-md bg-rose-50 p-3 text-sm text-rose-700">
            {error}
          </p>
        )}
      </section>
      <aside>
        <ResultView result={result} />
      </aside>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: ReactNode;
  label: string;
}) {
  return (
    <button
      className={`flex flex-1 items-center justify-center gap-2 rounded px-3 py-2 text-sm ${active ? "bg-white shadow-sm" : "text-slate-600"}`}
      onClick={onClick}
    >
      {icon} {label}
    </button>
  );
}

function classifyLocal(value: string): string {
  if (/^https?:\/\//i.test(value)) return "url";
  if (/^WIFI:/i.test(value)) return "wifi";
  if (/^BEGIN:VCARD/i.test(value)) return "vcard";
  return "text";
}
