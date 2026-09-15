/** @type {import('next').NextConfig} */
const nextConfig = {
  // Render 빌드 환경엔 Node 가 없어 정적 export 결과물(out/)을 로컬에서 빌드해
  // 커밋하고, FastAPI(webapi/main.py)가 그대로 서빙한다 (기존 Vite/dist 방식과 동일).
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
};

export default nextConfig;
