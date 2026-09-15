// Supabase 클라이언트 (브라우저 전용). 로그인/가입은 여기서 Supabase Auth와 직접
// 통신하고, FastAPI 호출 시에는 이 세션의 access_token만 Authorization 헤더로
// 넘긴다(lib/api.js). Next.js가 output:"export" 정적 사이트라 서버 세션/미들웨어가
// 없으므로 인증은 전부 클라이언트에서 처리한다.
//
// URL/publishable key는 공개 값(브라우저에 노출돼도 되는 anon key와 동일 성격, RLS로
// 보호)이라 API_BASE_URL과 같은 패턴으로 기본값을 소스에 두고 필요하면
// NEXT_PUBLIC_SUPABASE_URL / NEXT_PUBLIC_SUPABASE_ANON_KEY로 덮어쓴다.
import { createClient } from "@supabase/supabase-js";

const DEFAULT_SUPABASE_URL = "https://ogufiijusghepvidfsrm.supabase.co";
const DEFAULT_SUPABASE_ANON_KEY = "sb_publishable_iGTFwtZ8ENc0vuwCNxTB6A_tCZIhfTK";

export const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || DEFAULT_SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || DEFAULT_SUPABASE_ANON_KEY;

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
  },
});
