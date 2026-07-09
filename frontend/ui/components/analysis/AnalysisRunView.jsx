"use client";

import React, { useEffect, useRef, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_BGV_API_BASE_URL || "";

async function fetchJson(url) {
  const response = await fetch(url);
  const text = await response.text();
  if (!response.ok) {
    throw new Error(text || `Request failed (${response.status})`);
  }
  try {
    return JSON.parse(text);
  } catch {
    throw new Error(`Invalid API response: ${text.slice(0, 120)}`);
  }
}

function defaultStepLabel(step) {
  return step?.label || step?.key || "Step";
}

export default function AnalysisRunView({
  jobId,
  title,
  subtitle,
  steps = [],
  renderResult,
  statusPath = "/api/bgv/status",
  resultPath = "/api/bgv/result",
}) {
  const [job, setJob] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const routesRef = useRef({ statusPath, resultPath });

  useEffect(() => {
    routesRef.current = { statusPath, resultPath };
  }, [statusPath, resultPath]);

  useEffect(() => {
    if (!jobId) return;

    let mounted = true;

    const poll = async () => {
      try {
        const { statusPath: currentStatusPath, resultPath: currentResultPath } = routesRef.current;
        const state = await fetchJson(`${API_BASE}${currentStatusPath}/${jobId}`);
        if (!mounted) return;
        setJob(state);
        if (state.status === "done") {
          if (state.result_json) {
            setResult(state.result_json);
            return;
          }
          const data = await fetchJson(`${API_BASE}${currentResultPath}/${jobId}`);
          if (!mounted) return;
          setResult(data);
        } else if (state.status === "failed") {
          setError(state.error || "Job failed");
        }
      } catch (nextError) {
        if (mounted) {
          setError(String(nextError));
        }
      }
    };

    poll();
    const interval = setInterval(poll, 2500);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [jobId]);

  const completedSteps = job?.completed_steps || [];
  const remainingSteps = job?.remaining_steps || steps.slice(completedSteps.length);
  const currentStep = job?.current_step || (remainingSteps[0] ? defaultStepLabel(remainingSteps[0]) : null);
  const currentAgent = job?.current_agent || remainingSteps[0]?.agent || null;
  const progress = Number(job?.progress ?? 0);

  if (!jobId) return null;

  const displayTitle = job?.metadata?.company_name ? `${job.metadata.company_name} BGV` : title;
  const displaySubtitle = job?.metadata ? `${job.metadata.company_name || ""}${job.metadata.ticker ? ` (${job.metadata.ticker})` : ""}${subtitle ? ` · ${subtitle}` : ""}`.trim() : subtitle;

  return (
    <div
      className="min-h-[70vh] px-4 py-8 sm:px-6 lg:px-8"
      style={{
        backgroundImage:
          "radial-gradient(circle at top, rgba(251,191,36,0.18), transparent 30%), linear-gradient(180deg, #09111f 0%, #0f172a 55%, #f8fafc 55%)",
      }}
    >
      <div className="mx-auto max-w-7xl">
        <div className="mb-6 rounded-3xl border border-white/10 bg-white/8 p-6 text-white shadow-2xl shadow-black/10 backdrop-blur">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.32em] text-amber-300">Background Verification</p>
              <h1 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">{displayTitle}</h1>
              {displaySubtitle ? <p className="mt-2 max-w-3xl text-sm text-slate-300">{displaySubtitle}</p> : null}
            </div>
            <div className="rounded-2xl border border-white/10 bg-slate-950/60 px-5 py-4">
              <div className="text-3xl font-bold">{progress}%</div>
              <div className="text-xs uppercase tracking-[0.24em] text-slate-400">Progress</div>
            </div>
          </div>
          <div className="mt-6 h-3 overflow-hidden rounded-full bg-white/10">
            <div
              className="h-full rounded-full transition-all"
              style={{
                width: `${progress}%`,
                backgroundImage: "linear-gradient(90deg, #f59e0b 0%, #f97316 48%, #10b981 100%)",
              }}
            />
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <Stat label="Current status" value={job?.status || "queued"} />
            <Stat label="Current agent" value={currentAgent || "Waiting"} />
            <Stat label="Current step" value={currentStep || "Queued"} />
          </div>
          {job?.step_message ? <p className="mt-4 text-sm text-slate-300">{job.step_message}</p> : null}
        </div>

        <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-lg shadow-slate-900/5">
            <h2 className="text-lg font-semibold text-slate-950">Live Progress</h2>
            <p className="mt-1 text-sm text-slate-500">Updates are polled every few seconds while the crew runs.</p>

            <div className="mt-6 space-y-3">
              {steps.map((step, index) => {
                const stepLabel = defaultStepLabel(step);
                const isCompleted = completedSteps.some((item) => item.key === step.key);
                const isCurrent = currentStep === stepLabel || currentAgent === step.agent;
                const isRemaining = !isCompleted && !isCurrent;
                return (
                  <div key={step.key} className={`rounded-2xl border p-4 ${isCompleted ? "border-emerald-200 bg-emerald-50" : isCurrent ? "border-amber-200 bg-amber-50" : "border-slate-200 bg-slate-50"}`}>
                    <div className="flex items-start gap-3">
                      <div className={`mt-0.5 flex h-9 w-9 items-center justify-center rounded-full text-sm font-bold ${isCompleted ? "bg-emerald-500 text-white" : isCurrent ? "bg-amber-500 text-white" : "bg-slate-200 text-slate-600"}`}>
                        {index + 1}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="font-semibold text-slate-950">{stepLabel}</h3>
                          <span className="rounded-full bg-white px-2.5 py-0.5 text-xs font-medium text-slate-500">{step.agent}</span>
                          {isCompleted ? <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-700">Completed</span> : null}
                          {isCurrent ? <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-700">Running</span> : null}
                          {isRemaining ? <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-500">Pending</span> : null}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {error ? <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div> : null}
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-lg shadow-slate-900/5">
            <h2 className="text-lg font-semibold text-slate-950">Run Summary</h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <SummaryCard label="Queued" value={job?.created_at || "—"} />
              <SummaryCard label="Updated" value={job?.updated_at || "—"} />
              <SummaryCard label="Completed steps" value={completedSteps.length} />
              <SummaryCard label="Remaining steps" value={remainingSteps.length} />
            </div>

            {job?.status === "failed" ? (
              <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 p-4 text-red-700">
                <div className="font-semibold">Analysis failed</div>
                <p className="mt-1 text-sm">{job.error || "Unknown error"}</p>
              </div>
            ) : null}
          </div>
        </div>

        {/* Full-width final results area */}
        {job?.status === "done" && result && renderResult ? (
          <div className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-lg shadow-slate-900/5">
            <h2 className="text-lg font-semibold text-slate-950">Final Report</h2>
            <div className="mt-4">{renderResult(result, job)}</div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/8 px-4 py-3">
      <div className="text-[10px] font-semibold uppercase tracking-[0.28em] text-slate-400">{label}</div>
      <div className="mt-1 text-sm font-semibold text-white">{value}</div>
    </div>
  );
}

function SummaryCard({ label, value }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{label}</div>
      <div className="mt-2 text-base font-semibold text-slate-950">{value}</div>
    </div>
  );
}
