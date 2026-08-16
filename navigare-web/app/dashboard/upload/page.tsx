"use client";

import { useState, useRef, useCallback } from "react";
import Card from "@/components/Card";
import Callout from "@/components/Callout";
import SectionHeader from "@/components/SectionHeader";
import Icon from "@/components/Icon";
import { uploadFile } from "@/lib/api";

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
      className="text-xs px-3 py-1.5 rounded-lg border border-border text-muted hover:text-blue hover:border-blue transition inline-flex items-center gap-1.5"
    >
      <Icon name="download" size={14} /> Download Sample
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
    <Card hover>
      <div className="flex items-center justify-between mb-4">
        <SectionHeader title={title} className="mt-0 mb-0" />
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
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
          dragActive ? "border-purple bg-purple/5 scale-[1.01]" : "border-border hover:border-purple/40 hover:bg-purple/5"
        }`}
      >
        <div className={`text-4xl mb-3 transition-transform text-muted ${dragActive ? "scale-110" : ""}`}><Icon name={icon} size={40} /></div>
        <p className="text-sm text-muted mb-2">{dragActive ? "Drop your CSV here!" : "Drag & drop your CSV, or click to browse"}</p>
        <p className="text-[11px] text-muted/60 mb-4">Max 10MB · .csv format only</p>
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])}
          className="hidden"
        />
        {!file && <div className="text-sm font-medium text-purple opacity-60">No file selected</div>}
      </div>
      {file && (
        <div className="mt-4 flex items-center justify-between gap-3 p-3 bg-bg rounded-xl border border-border animate-fade-in">
          <div className="flex items-center gap-2">
            <Icon name="file" size={20} className="text-muted" />
            <div>
              <div className="text-sm font-medium text-text">{file.name}</div>
              <div className="text-xs text-muted">{(file.size / 1024).toFixed(1)} KB</div>
            </div>
          </div>
          <button
            onClick={onUpload}
            disabled={loading}
            className="btn-primary text-sm disabled:opacity-50"
          >
            {loading ? "Uploading..." : `Upload ${label}`}
          </button>
        </div>
      )}
    </Card>
  );
}

export default function UploadPage() {
  const [txnFile, setTxnFile] = useState<File | null>(null);
  const [invFile, setInvFile] = useState<File | null>(null);
  const [status, setStatus] = useState<UploadStatus>(null);
  const [loading, setLoading] = useState(false);

  const handleUpload = async (file: File, type: "txn" | "inv") => {
    setLoading(true);
    setStatus(null);
    try {
      const endpoint = type === "txn" ? "/api/upload/transactions" : "/api/upload/inventory";
      await uploadFile(endpoint, file, "file");
      setStatus({
        type: "success",
        message: `${type === "txn" ? "Transactions" : "Inventory"} uploaded successfully: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`,
      });
      if (type === "txn") setTxnFile(null);
      else setInvFile(null);
    } catch (e) {
      setStatus({ type: "error", message: e instanceof Error ? e.message : "Upload failed" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-[22px] font-extrabold text-text mb-1 tracking-tight">Upload Your Data</h1>
      <p className="text-[13.5px] text-muted mb-6">Replace the sample data with your own sales and inventory CSVs.</p>

      {status && (
        <Callout variant={status.type === "success" ? "good" : "danger"} className="mb-6 animate-fade-in">
          {status.message}
        </Callout>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <UploadZone
          icon="file"
          title="Sales / Transactions CSV"
          file={txnFile}
          onFile={setTxnFile}
          onUpload={() => txnFile && handleUpload(txnFile, "txn")}
          loading={loading}
          label="Transactions"
        />
        <UploadZone
          icon="box"
          title="Inventory CSV"
          file={invFile}
          onFile={setInvFile}
          onUpload={() => invFile && handleUpload(invFile, "inv")}
          loading={loading}
          label="Inventory"
        />
      </div>

      <Card hover>
        <SectionHeader title="Required Column Names" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Icon name="file" size={16} className="text-muted" />
              <div className="text-xs font-semibold text-muted uppercase tracking-wider">Transactions</div>
            </div>
            <code className="block bg-bg p-4 rounded-xl text-xs text-text leading-relaxed border border-border">
              Transaction_Date, Transaction_ID, Customer_ID,<br />
              Product_ID, Product_Name, Quantity, Line_Total_USD, Category
            </code>
          </div>
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Icon name="box" size={16} className="text-muted" />
              <div className="text-xs font-semibold text-muted uppercase tracking-wider">Inventory</div>
            </div>
            <code className="block bg-bg p-4 rounded-xl text-xs text-text leading-relaxed border border-border">
              Product_ID, Product_Name, Category,<br />
              Current_Stock, Retail_Price, Cost_Price, Reorder_Level
            </code>
          </div>
        </div>
      </Card>
    </div>
  );
}
