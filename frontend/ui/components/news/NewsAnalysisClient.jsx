"use client";

import React from "react";
import AnalysisRunView from "../analysis/AnalysisRunView";
import NewsReportView from "./NewsReportView";
import { NEWS_ANALYSIS_STEPS } from "./newsConfig";

export default function NewsAnalysisClient({ jobId }) {
  return (
    <AnalysisRunView
      jobId={jobId}
      title="News Sentiment Analysis"
      subtitle="Live news sentiment analysis powered by FinBERT with deep context evaluation."
      steps={NEWS_ANALYSIS_STEPS}
      statusPath="/api/news/status"
      resultPath="/api/news/result"
      renderResult={(result) => <NewsReportView result={result} />}
    />
  );
}
