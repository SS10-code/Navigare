"use client";

import { useRef, useState } from "react";
import Papa from "papaparse";
import { analytics } from "@/lib/analytics";

interface UploadCSVProps {
  onDataParsed: (data: Record<string, unknown>[], fileName: string) => void;
  accept?: string;
  label?: string;
}

export default function UploadCSV({
  onDataParsed,
  accept = ".csv",
  label = "Upload CSV",
}: UploadCSVProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = (file: File) => {
    setIsLoading(true);
    setError(null);
    setFileName(file.name);

    Papa.parse<Record<string, unknown>>(file, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        const data = results.data as Record<string, unknown>[];
        setIsLoading(false);
        onDataParsed(data, file.name);

        analytics.track("csv_upload", {
          fileName: file.name,
          rowCount: data.length,
          columnCount: results.meta.fields?.length || 0,
          fileSizeKB: Math.round(file.size / 1024),
          parseErrors: results.errors.length,
        });
      },
      error: (err) => {
        setIsLoading(false);
        setError(err.message);
        analytics.track("csv_upload", {
          fileName: file.name,
          error: err.message,
        });
      },
    });
  };

  return (
    <div className="flex flex-col gap-2">
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
          e.target.value = "";
        }}
      />
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        disabled={isLoading}
        className="px-4 py-2 bg-purple text-white rounded-md text-sm font-medium hover:bg-purple/90 disabled:opacity-50"
      >
        {isLoading ? "Parsing..." : label}
      </button>
      {fileName && !error && (
        <span className="text-xs text-green">Loaded: {fileName}</span>
      )}
      {error && <span className="text-xs text-red">Error: {error}</span>}
    </div>
  );
}
