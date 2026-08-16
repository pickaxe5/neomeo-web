export function ErrorBanner({ message }: { message: string | null }) {
  if (!message) return null;
  return <div className="error-banner">{message}</div>;
}

export function errorMessage(err: unknown): string {
  if (err instanceof Error) return err.message;
  const lang = localStorage.getItem("neomeo_lang");
  return lang === "en" ? "Something went wrong." : "알 수 없는 오류가 발생했습니다.";
}
