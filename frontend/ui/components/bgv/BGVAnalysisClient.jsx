"use client";

import React from "react";
import AnalysisRunView from "../analysis/AnalysisRunView";
import BGVReportView from "./BGVReportView";
import { BGV_ANALYSIS_STEPS } from "./bgvConfig";

export default function BGVAnalysisClient({ jobId }) {
  return (
    <AnalysisRunView
      jobId={jobId}
      title="BGV Analysis"
      subtitle="Live background verification with agent-level progress and a structured company report."
      steps={BGV_ANALYSIS_STEPS}
      renderResult={(result) => <BGVReportView result={result} />}
    />
  );
}
