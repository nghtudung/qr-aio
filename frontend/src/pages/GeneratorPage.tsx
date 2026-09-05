import { Download, ImagePlus, RefreshCw } from "lucide-react";
import { ChangeEvent, useEffect, useMemo, useState } from "react";
import { Field } from "../components/Field";
import {
  GenerateRequest,
  GenerateResponse,
  downloadBase64,
  generateQr,
} from "../lib/api";

const initialRequest: GenerateRequest = {
  data_type: "url",
  value: "https://example.com",
  error_correction: "H",
  width: 1024,
  height: 1024,
  foreground: "#111827",
  background: "#ffffff",
  transparent_background: false,
  gradient: {
    enabled: false,
    start: "#111827",
    end: "#0f766e",
    direction: "diagonal",
  },
  module_style: "square",
  finder_style: "rounded",
  logo: {
    enabled: false,
    data_url: null,
    size_percent: 15,
    padding: 14,
    rounded_container: true,
    border: false,
    background: "#ffffff",
  },
  export_format: "png",
  pdf: {
    page_size: "A4",
    custom_width_mm: null,
    custom_height_mm: null,
    title: null,
    description: null,
    multiple_per_page: 1,
  },
};

export function GeneratorPage() {
  const [request, setRequest] = useState<GenerateRequest>(initialRequest);
  const [response, setResponse] = useState<GenerateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const previewSrc = useMemo(() => {
    if (
      !response ||
      !response.media_type.startsWith("image/") ||
      response.media_type.includes("svg")
    )
      return null;
    return `data:${response.media_type};base64,${response.data}`;
  }, [response]);

  useEffect(() => {
    const id = window.setTimeout(() => void submit(false), 350);
    return () => window.clearTimeout(id);
  }, [request]);

  const patch = (update: Partial<GenerateRequest>) =>
    setRequest((current) => ({ ...current, ...update }));

  async function submit(download: boolean) {
    setLoading(true);
    setError(null);
    try {
      const data = await generateQr(request);
      setResponse(data);
      if (download) downloadBase64(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to generate QR code",
      );
    } finally {
      setLoading(false);
    }
  }

  async function logoSelected(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () =>
      setRequest((current) => ({
        ...current,
        logo: {
          ...current.logo,
          enabled: true,
          data_url: String(reader.result),
        },
      }));
    reader.readAsDataURL(file);
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[390px_1fr]">
      <section className="panel rounded-md p-4">
        <div className="grid gap-4">
          <Field label="Data type">
            <select
              className="control"
              value={request.data_type}
              onChange={(event) => patch({ data_type: event.target.value })}
            >
              {[
                "text",
                "url",
                "email",
                "phone",
                "sms",
                "wifi",
                "vcard",
                "json",
              ].map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </Field>
          <Field label="Payload">
            <textarea
              className="control min-h-28 resize-y"
              value={request.value}
              onChange={(event) => patch({ value: event.target.value })}
            />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Width">
              <input
                className="control"
                type="number"
                value={request.width}
                onChange={(event) =>
                  patch({ width: Number(event.target.value) })
                }
              />
            </Field>
            <Field label="Height">
              <input
                className="control"
                type="number"
                value={request.height}
                onChange={(event) =>
                  patch({ height: Number(event.target.value) })
                }
              />
            </Field>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Foreground">
              <input
                className="control h-10"
                type="color"
                value={request.foreground}
                onChange={(event) => patch({ foreground: event.target.value })}
              />
            </Field>
            <Field label="Background">
              <input
                className="control h-10"
                type="color"
                value={request.background}
                onChange={(event) => patch({ background: event.target.value })}
              />
            </Field>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Module style">
              <select
                className="control"
                value={request.module_style}
                onChange={(event) =>
                  patch({
                    module_style: event.target
                      .value as GenerateRequest["module_style"],
                  })
                }
              >
                <option>square</option>
                <option>rounded</option>
                <option>circle</option>
              </select>
            </Field>
            <Field label="Finder style">
              <select
                className="control"
                value={request.finder_style}
                onChange={(event) =>
                  patch({
                    finder_style: event.target
                      .value as GenerateRequest["finder_style"],
                  })
                }
              >
                <option>square</option>
                <option>rounded</option>
                <option>circle</option>
              </select>
            </Field>
          </div>
          <Field label="Error correction">
            <select
              className="control"
              value={request.error_correction}
              onChange={(event) =>
                patch({
                  error_correction: event.target
                    .value as GenerateRequest["error_correction"],
                })
              }
            >
              <option>L</option>
              <option>M</option>
              <option>Q</option>
              <option>H</option>
            </select>
          </Field>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={request.gradient.enabled}
              onChange={(event) =>
                patch({
                  gradient: {
                    ...request.gradient,
                    enabled: event.target.checked,
                  },
                })
              }
            />{" "}
            Gradient foreground
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={request.transparent_background}
              onChange={(event) =>
                patch({ transparent_background: event.target.checked })
              }
            />{" "}
            Transparent background
          </label>
          <div className="rounded-md border border-line bg-slate-50 p-3">
            <div className="mb-3 flex items-center justify-between">
              <span className="label">Logo</span>
              <label className="flex cursor-pointer items-center gap-2 rounded-md border border-line bg-white px-3 py-2 text-sm">
                <ImagePlus size={16} /> PNG or SVG
                <input
                  className="hidden"
                  type="file"
                  accept="image/png,image/svg+xml"
                  onChange={logoSelected}
                />
              </label>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Size %">
                <input
                  className="control"
                  type="number"
                  min={10}
                  max={25}
                  value={request.logo.size_percent}
                  onChange={(event) =>
                    setRequest((current) => ({
                      ...current,
                      logo: {
                        ...current.logo,
                        size_percent: Number(event.target.value),
                      },
                    }))
                  }
                />
              </Field>
              <Field label="Padding">
                <input
                  className="control"
                  type="number"
                  value={request.logo.padding}
                  onChange={(event) =>
                    setRequest((current) => ({
                      ...current,
                      logo: {
                        ...current.logo,
                        padding: Number(event.target.value),
                      },
                    }))
                  }
                />
              </Field>
            </div>
          </div>
          <Field label="Export format">
            <select
              className="control"
              value={request.export_format}
              onChange={(event) =>
                patch({
                  export_format: event.target
                    .value as GenerateRequest["export_format"],
                })
              }
            >
              <option>png</option>
              <option>jpg</option>
              <option>webp</option>
              <option>svg</option>
              <option>eps</option>
              <option>pdf</option>
            </select>
          </Field>
          <button
            className="flex items-center justify-center gap-2 rounded-md bg-ink px-4 py-3 text-sm font-semibold text-white"
            onClick={() => void submit(true)}
          >
            <Download size={17} /> Export
          </button>
        </div>
      </section>
      <section className="panel rounded-md p-6">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">Live preview</h2>
            <p className="text-sm text-slate-500">
              {response?.readable ? "Readable" : "Needs adjustment"}
            </p>
          </div>
          {loading && (
            <RefreshCw className="animate-spin text-slate-400" size={18} />
          )}
        </div>
        <div className="grid min-h-[520px] place-items-center rounded-md border border-dashed border-line bg-white p-6">
          {previewSrc ? (
            <img
              className="max-h-[480px] w-auto max-w-full"
              src={previewSrc}
              alt="QR code preview"
            />
          ) : (
            <p className="text-sm text-slate-500">
              Preview available for PNG, JPG, and WEBP exports.
            </p>
          )}
        </div>
        {response?.warnings.map((warning) => (
          <p
            key={warning}
            className="mt-3 rounded-md bg-amber-50 p-3 text-sm text-amber-800"
          >
            {warning}
          </p>
        ))}
        {error && (
          <p className="mt-3 rounded-md bg-rose-50 p-3 text-sm text-rose-700">
            {error}
          </p>
        )}
      </section>
    </div>
  );
}
