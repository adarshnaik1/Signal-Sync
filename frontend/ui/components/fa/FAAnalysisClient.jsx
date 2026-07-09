"use client";

import React from "react";
import AnalysisRunView from "../analysis/AnalysisRunView";
import FAReportView from "./FAReportView";
import { FA_ANALYSIS_STEPS } from "./faConfig";

export default function FAAnalysisClient({ jobId }) {
  return (
    <AnalysisRunView
      jobId={jobId}
      title="Fundamental Analysis"
      subtitle="Live fundamental analysis with agent-level progress and a structured investment report."
      steps={FA_ANALYSIS_STEPS}
      statusPath="/api/fa/status"
      resultPath="/api/fa/result"
      renderResult={(result) => <FAReportView result={result} />}
    />
  );
}
