"use client";

// 이메일/비밀번호 로그인·가입만 지원(MVP). Google OAuth 등은 추후 확장.
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Card from "@/components/ui/Card";
import { ErrorMessage, Hint } from "@/components/ui/StatusMessage";
import { useAuth } from "@/lib/authContext";

export default function LoginPage() {
  const router = useRouter();
  const { user, loading, signInWithPassword, signUpWithPassword } = useAuth();

  const [mode, setMode] = useState("signin"); // "signin" | "signup"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [signupDone, setSignupDone] = useState(false);

  useEffect(() => {
    if (!loading && user) router.replace("/watchlist");
  }, [loading, user, router]);

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      if (mode === "signin") {
        await signInWithPassword(email, password);
        router.replace("/watchlist");
      } else {
        await signUpWithPassword(email, password);
        setSignupDone(true);
      }
    } catch (err) {
      setError(err.message || "요청에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-sm space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{mode === "signin" ? "로그인" : "회원가입"}</h1>
        <p className="mt-1.5 text-[14px] text-ink-dim">관심종목과 알림을 사용하려면 로그인이 필요합니다.</p>
      </div>

      <Card>
        <div className="mb-5 flex rounded-md border border-border bg-bg-raised p-1">
          <button
            type="button"
            onClick={() => { setMode("signin"); setError(null); setSignupDone(false); }}
            className={`flex-1 rounded px-3 py-1.5 text-[13px] transition-colors ${
              mode === "signin" ? "bg-amber font-semibold text-[#1A1000]" : "text-ink-dim hover:text-ink"
            }`}
          >
            로그인
          </button>
          <button
            type="button"
            onClick={() => { setMode("signup"); setError(null); setSignupDone(false); }}
            className={`flex-1 rounded px-3 py-1.5 text-[13px] transition-colors ${
              mode === "signup" ? "bg-amber font-semibold text-[#1A1000]" : "text-ink-dim hover:text-ink"
            }`}
          >
            회원가입
          </button>
        </div>

        {signupDone ? (
          <Hint>가입 확인 이메일을 보냈습니다. 메일함에서 링크를 확인한 뒤 로그인해주세요.</Hint>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="mb-1.5 block text-[12.5px] text-ink-faint">이메일</label>
              <input
                id="email"
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-md border border-border bg-bg-raised px-3 py-2.5 text-sm text-ink placeholder:text-ink-faint focus:border-amber-dim focus:outline-none"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label htmlFor="password" className="mb-1.5 block text-[12.5px] text-ink-faint">비밀번호</label>
              <input
                id="password"
                type="password"
                required
                minLength={6}
                autoComplete={mode === "signin" ? "current-password" : "new-password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-md border border-border bg-bg-raised px-3 py-2.5 text-sm text-ink placeholder:text-ink-faint focus:border-amber-dim focus:outline-none"
                placeholder="6자 이상"
              />
            </div>

            {error && <ErrorMessage>{error}</ErrorMessage>}

            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-md bg-amber px-5 py-2.5 font-semibold text-[#1A1000] transition-opacity disabled:opacity-40"
            >
              {submitting ? "처리 중..." : mode === "signin" ? "로그인" : "가입하기"}
            </button>
          </form>
        )}
      </Card>
    </div>
  );
}
