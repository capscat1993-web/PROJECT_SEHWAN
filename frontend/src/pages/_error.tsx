import type { NextPageContext } from "next";

type ErrorPageProps = {
  statusCode?: number;
};

function ErrorPage({ statusCode }: Readonly<ErrorPageProps>) {
  return (
    <main
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        padding: "40px 20px",
        background: "#f1f5f9",
        color: "#0f172a",
        fontFamily: '"Segoe UI", "Apple SD Gothic Neo", "Noto Sans KR", sans-serif',
      }}
    >
      <section
        style={{
          width: "min(520px, 100%)",
          padding: "32px",
          borderRadius: "20px",
          background: "#ffffff",
          border: "1px solid #d8e0ea",
          boxShadow: "0 8px 24px rgba(15, 23, 42, 0.04)",
          textAlign: "center",
        }}
      >
        <p style={{ margin: 0, color: "#56789c", fontSize: "0.82rem", fontWeight: 700, letterSpacing: "0.08em" }}>
          SERVICE NOTICE
        </p>
        <h1 style={{ margin: "12px 0 10px", fontSize: "2rem", letterSpacing: "-0.04em" }}>
          {statusCode ? `${statusCode} 오류가 발생했습니다.` : "예상치 못한 오류가 발생했습니다."}
        </h1>
        <p style={{ margin: 0, color: "#64748b", lineHeight: 1.7 }}>
          잠시 후 다시 시도해주세요. 문제가 계속되면 관리자에게 문의해 주세요.
        </p>
      </section>
    </main>
  );
}

ErrorPage.getInitialProps = ({ res, err }: NextPageContext) => {
  const statusCode = res?.statusCode ?? err?.statusCode ?? 500;
  return { statusCode };
};

export default ErrorPage;
