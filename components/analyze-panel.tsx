"use client";

import React, { useMemo, useRef, useState } from "react";
import { Button } from "./ui/button";

export type DetectResult = {
  imageUrl: string; // annotated
  originalImageUrl: string;
  summary: string;
  counts: Record<string, number>;
  total: number;
  detections: Array<any>;
  upload: { filename: string; stored: string };
};

export function AnalyzePanel({
  onAnalyzed,
  onAsk,
}: {
  onAnalyzed: (result: DetectResult) => void;
  onAsk?: (prompt: string, result: DetectResult) => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [serverAnnotatedUrl, setServerAnnotatedUrl] = useState<string | null>(
    null,
  );
  const [serverOriginalUrl, setServerOriginalUrl] = useState<string | null>(
    null,
  );
  const [result, setResult] = useState<DetectResult | null>(null);
  const [showOriginal, setShowOriginal] = useState(false);

  const inputRef = useRef<HTMLInputElement>(null);

  const currentImage = useMemo(() => {
    // Before analysis, show the local preview if available.
    // After analysis, show either annotated or original based on toggle.
    if (serverAnnotatedUrl || serverOriginalUrl) {
      return showOriginal ? serverOriginalUrl : serverAnnotatedUrl;
    }
    return previewUrl;
  }, [serverAnnotatedUrl, serverOriginalUrl, previewUrl, showOriginal]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null;
    setFile(f);
    if (f) {
      const url = URL.createObjectURL(f);
      setPreviewUrl(url);
      setServerAnnotatedUrl(null);
      setServerOriginalUrl(null);
    } else {
      setPreviewUrl(null);
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;
    try {
      setIsAnalyzing(true);
      const form = new FormData();
      form.append("file", file);
      const res = await fetch("/api/detect", {
        method: "POST",
        body: form,
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `Analyze failed with ${res.status}`);
      }
      const data: DetectResult = await res.json();
      setServerAnnotatedUrl(data.imageUrl);
      setServerOriginalUrl(data.originalImageUrl);
      setResult(data);
      setShowOriginal(false);
      onAnalyzed(data);
    } catch (err) {
      console.error(err);
      alert("Failed to analyze image. See console for details.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto px-4">
      <div className="flex flex-col gap-4 border rounded-xl p-4 bg-muted/40 mb-4">
        <div className="flex flex-wrap items-center gap-2">
          <input
            ref={inputRef}
            type="file"
            accept="image/*,.tif,.tiff,.jp2,.jpeg,.jpg,.png,.hdf"
            onChange={handleFileChange}
            className="w-full sm:w-auto"
          />
          <Button
            onClick={handleAnalyze}
            disabled={!file || isAnalyzing}
            variant="default"
            className="w-full sm:w-auto"
          >
            {isAnalyzing ? "Analyzing..." : "Analyze"}
          </Button>

          {(serverAnnotatedUrl || serverOriginalUrl) && (
            <Button
              type="button"
              variant="outline"
              className="w-full sm:w-auto"
              onClick={() => setShowOriginal((v) => !v)}
            >
              {showOriginal ? "Show annotated" : "Show original"}
            </Button>
          )}

          {result && onAsk && (
            <Button
              type="button"
              variant="secondary"
              className="w-full sm:w-auto"
              onClick={() =>
                onAsk(
                  "Explain these detections and any anomalies I should note.",
                  result,
                )
              }
            >
              Ask about this
            </Button>
          )}
        </div>

        {/* Image viewer */}
        {currentImage && (
          <div className="flex flex-col gap-2">
            <div
              className={`relative overflow-hidden rounded-lg bg-background border cursor-pointer ${
                expanded ? "h-auto" : "h-72"
              }`}
              onClick={() => setExpanded((v) => !v)}
              title={expanded ? "Click to collapse" : "Click to expand"}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={currentImage}
                alt="preview"
                className={`w-full object-contain ${expanded ? "max-h-[70vh]" : "h-full"}`}
              />
            </div>
            <div className="text-xs text-muted-foreground">
              {expanded ? "Click image to collapse" : "Click image to expand"}
            </div>
          </div>
        )}

        {/* Summary and counts */}
        {result && (
          <div className="flex flex-col gap-2">
            <div className="text-sm font-medium">Result summary</div>
            <div className="text-sm">{result.summary}</div>
            <div className="text-xs text-muted-foreground">Total: {result.total}</div>
            {Object.keys(result.counts || {}).length > 0 && (
              <div className="text-xs">
                <div className="font-medium mb-1">Counts</div>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-1">
                  {Object.entries(result.counts).map(([k, v]) => (
                    <div key={k} className="flex items-center justify-between rounded border px-2 py-1 bg-background">
                      <span className="truncate mr-2">{k}</span>
                      <span className="font-mono">{v as number}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
