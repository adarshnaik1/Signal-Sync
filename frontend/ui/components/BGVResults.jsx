"use client";

import React, { useState, useEffect } from "react";

const API_BASE = process.env.NEXT_PUBLIC_BGV_API_BASE_URL || "";

async function fetchJson(url) {
  const res = await fetch(url);
  const text = await res.text();
  if (!res.ok) {
    throw new Error(text || `Request failed (${res.status})`);
  }
  try {
    return JSON.parse(text);
  } catch {
    throw new Error(`Invalid API response: ${text.slice(0, 120)}`);
  }
}

export default function BGVResults({ jobId }) {
  const [status, setStatus] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!jobId) return;

    let mounted = true;

    const poll = async () => {
      try {
        const json = await fetchJson(`${API_BASE}/api/bgv/status/${jobId}`);
        if (!mounted) return;
        setStatus(json.status);
        if (json.status === "done") {
          const data = await fetchJson(`${API_BASE}/api/bgv/result/${jobId}`);
          setResult(data);
        } else if (json.status === "failed") {
          setError(json.error || "Job failed");
        }
      } catch (e) {
        setError(String(e));
      }
    };

    // poll until done or failed
    const interval = setInterval(poll, 3000);
    // initial poll
    poll();

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [jobId]);

  if (!jobId) return null;

  if (error) return <div className="p-4 rounded border bg-red-50 text-red-700">Error: {error}</div>;
  if (!status) return <div className="p-4">Starting analysis...</div>;

  if (status === "running") return <div className="p-4">Analysis running... (this may take a few minutes)</div>;

  if (status === "done" && result) {
    const { final_verdict, scores, findings } = result;
    return (
      <div className="rounded-2xl border p-4 bg-white">
        <h3 className="text-lg font-semibold">BGV Analysis Result</h3>
        {final_verdict ? <div className="mt-2 font-medium">{final_verdict}</div> : null}
        {scores ? (
          <div className="mt-3 grid grid-cols-2 gap-2">
            {Object.entries(scores).map(([k, v]) => (
              <div key={k} className="rounded p-2 bg-slate-50">
                <div className="text-xs text-slate-500">{k.replace(/_/g, ' ')}</div>
                <div className="font-semibold">{v}</div>
              </div>
            ))}
          </div>
        ) : null}

        {findings ? (
          <div className="mt-3">
            <h4 className="font-semibold">Key Findings</h4>
            <pre className="whitespace-pre-wrap text-sm">{JSON.stringify(findings, null, 2)}</pre>
          </div>
        ) : null}

        <div className="mt-3">
          <a className="text-sm underline" href={`${API_BASE}/api/bgv/result/${jobId}`} target="_blank" rel="noreferrer">Download JSON</a>
        </div>
      </div>
    );
  }

  return <div className="p-4">Status: {status}</div>;
}
