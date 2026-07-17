import { verificationMeta, type VerificationStatus } from "@/lib/api";

export default function VerificationBadge({ status }: { status: VerificationStatus }) {
  const meta = verificationMeta(status);
  return <span className={`pill ${meta.className}`}>{meta.label}</span>;
}
