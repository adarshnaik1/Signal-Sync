"use client";

import React from "react";
import AnalysisRunView from "../analysis/AnalysisRunView";
import TAReportView from "./TAReportView";
import { TA_ANALYSIS_STEPS } from "./taConfig";

export default function TAAnalysisClient({ jobId }) {
  return (
    <AnalysisRunView
      jobId={jobId}
      title="Technical Analysis"
      subtitle="Live TA execution with progress tracking and a structured signal report."
      steps={TA_ANALYSIS_STEPS}
      statusPath="/api/ta/status"
      resultPath="/api/ta/result"
      renderResult={(result) => <TAReportView result={result} />}
    />
  );
}