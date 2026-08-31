"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import Card from "@/components/Card";
import Callout from "@/components/Callout";
import SectionHeader from "@/components/SectionHeader";
import Icon from "@/components/Icon";
import { uploadFile, apiFetch } from "@/lib/api";
import { useRouter } from "next/navigation";
import { setOnboarded } from "@/lib/auth";

type UploadStatus = { type: "success" | "error"; message: string } | null;

function DownloadSampleCSV({ type }: { type: "transactions" | "inventory" }) {
  const content =
    type === "transactions"
      ? "Transaction_Date,Transaction_ID,Customer_ID,Product_ID,Product_Name,Quantity,Line_Total_USD,Category\n2026-07-01,T001,C001,P001,Sourdough Loaf,2,12.00,Bread\n2026-07-01,T002,C002,P002,Croissant,3,9.00,Pastry\n2026-07-02,T003,C001,P003,Latte,1,4.50,Coffee"
      : "Product_ID,Product_Name,Category,Current_Stock,Retail_Price,Cost_Price,Reorder_Level\n1,Sourdough Loaf,Bread,35,6.00,2.50,10\n2,Croissant,Pastry,8,3.00,1.20,10\n3,Latte,Coffee,50,4.50,1.50,15";

  const handleClick = () => {
    const blob = new Blob([content], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `sample_${type}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <button
      onClick={handleClick}
      className="text-xs px-3 py-2 border-2 border-border text-muted hover:text-accent hover:border-accent transition no-underline"
    >
      <Icon name="download" size={14} className="inline mr-1" /> Sample
    </button>
  );
}

function UploadZone({
  icon,
  title,
  file,
  onFile,
  onUpload,
  loading,
  label,
}: {
  icon: "file" | "box";
  title: string;
  file: File | null;
  onFile: (f: File) => void;
  onUpload: () => void;
  loading: boolean;
  label: string;
}) {
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);
      const f = e.dataTransfer.files?.[0];
      if (f && f.name.endsWith(".csv")) onFile(f);
    },
    [onFile]
  );

  return (
    <div className="border-2 border-border bg-panel">
      <div className="flex items-center justify-between p-4 border-b-2 border-border">
        <h3 className="text-headline text-sm font-bold uppercase tracking-wide">{title}</h3>
        <DownloadSampleCSV type={title.includes("Sales") || title.includes("Transactions") ? "transactions" : "inventory"} />
      </div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`p-8 text-center cursor-pointer transition-colors border-l-4 ${
          dragActive ? "border-l-accent bg-paper" : "border-l-transparent hover:bg-paper"
        }`}
      >
        <div className="text-muted mb-3"><Icon name={icon} size={36} /></div>
        <p className="text-body text-sm text-ink mb-1 font-medium">{dragActive ? "Drop CSV here" : "Drag & drop or click to browse"}</p>
        <p className="text-caption text-muted text-[10px]">Max 10MB · CSV only</p>
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])}
          className="hidden"
        />
        {!file && <div className="text-xs text-muted mt-3 font-mono">No file selected</div>}
      </div>
      {file && (
        <div className="p-4 bg-paper border-t-2 border-border flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Icon name="file" size={18} className="text-muted" />
            <div>
              <div className="text-sm font-semibold text-ink">{file.name}</div>
              <div className="text-xs text-muted font-mono">{(file.size / 1024).toFixed(1)} KB</div>
            </div>
          </div>
          <button
            onClick={onUpload}
            disabled={loading}
            className="btn-primary text-xs"
          >
            {loading ? "Uploading..." : `Upload ${label}`}
          </button>
        </div>
      )}
    </div>
  );
}

export default function UploadPage() {
  const [txnFile, setTxnFile] = useState<File | null>(null);
  const [invFile, setInvFile] = useState<File | null>(null);
  const [status, setStatus] = useState<UploadStatus>(null);
  const [loading, setLoading] = useState(false);
  const [onboarding, setOnboarding] = useState(false);
  const router = useRouter();

  useEffect(() => {
    if (typeof window !== "undefined") {
      const urlOnboarding = window.location.search.includes("onboarding=true") || window.location.search.includes("guest=true");
      const cookieOnboarding = !document.cookie.split("; ").some((c) => c.startsWith("navigare_onboarded=true"));
      setOnboarding(urlOnboarding || cookieOnboarding);
    }
  }, []);

  const markOnboarded = async () => {
    setOnboarded(true);
    try {
      await apiFetch("/counters/onboarded", { method: "POST" });
    } catch {}
    setTimeout(() => {
      window.location.href = "/dashboard";
    }, 150);
  };

  const handleUpload = async (file: File, type: "txn" | "inv") => {
    setLoading(true);
    setStatus(null);
    try {
      const endpoint = type === "txn" ? "/api/upload/transactions" : "/api/upload/inventory";
      await uploadFile(endpoint, file, "file");
      setStatus({
        type: "success",
        message: `${type === "txn" ? "Transactions" : "Inventory"} uploaded: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`,
      });
      if (type === "txn") setTxnFile(null);
      else setInvFile(null);
      if (onboarding) {
        setTimeout(() => markOnboarded(), 1500);
      }
    } catch (e) {
      setStatus({ type: "error", message: e instanceof Error ? e.message : "Upload failed" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-display text-3xl font-bold uppercase tracking-tight mb-2">
          {onboarding ? "Upload your data" : "Upload"}
        </h1>
        <p className="text-body text-sm text-muted max-w-lg">
          {onboarding
            ? "Upload your sales and inventory data to unlock the full dashboard. This only takes a minute."
            : "Replace the sample data with your own sales and inventory CSVs."}
        </p>
      </div>

      {status && (
        <Callout variant={status.type === "success" ? "good" : "danger"} className="mb-6">
          {status.message}
        </Callout>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <UploadZone
          icon="file"
          title="Sales / Transactions"
          file={txnFile}
          onFile={setTxnFile}
          onUpload={() => txnFile && handleUpload(txnFile, "txn")}
          loading={loading}
          label="Transactions"
        />
        <UploadZone
          icon="box"
          title="Inventory"
          file={invFile}
          onFile={setInvFile}
          onUpload={() => invFile && handleUpload(invFile, "inv")}
          loading={loading}
          label="Inventory"
        />
      </div>

      {onboarding && (
        <Card className="mb-8">
          <SectionHeader title="Required columns" />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <div className="text-caption text-muted mb-2">Transactions</div>
              <code className="block bg-paper p-4 text-xs text-ink leading-relaxed border-2 border-border">
                Transaction_Date, Transaction_ID, Customer_ID,<br />
                Product_ID, Product_Name, Quantity, Line_Total_USD, Category
              </code>
            </div>
            <div>
              <div className="text-caption text-muted mb-2">Inventory</div>
              <code className="block bg-paper p-4 text-xs text-ink leading-relaxed border-2 border-border">
                Product_ID, Product_Name, Category,<br />
                Current_Stock, Retail_Price, Cost_Price, Reorder_Level
              </code>
            </div>
          </div>
        </Card>
      )}

      <div className="flex items-center justify-between pt-4 border-t-2 border-border">
        <div className="text-xs text-muted">
          {onboarding
            ? "Don't have your data ready? Skip to explore with sample data."
            : "Download the sample CSVs above to see the expected format."}
        </div>
        {onboarding && (
          <button onClick={markOnboarded} className="btn-secondary text-xs">
            Skip for now
          </button>
        )}
      </div>
    </div>
  );
}
