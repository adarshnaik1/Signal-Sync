import BGVAnalysisClient from "../../../../components/bgv/BGVAnalysisClient";

export default async function BGVAnalysisPage({ params }) {
  const { jobId } = (await params) ?? {};

  return <BGVAnalysisClient jobId={String(jobId || "")} />;
}
