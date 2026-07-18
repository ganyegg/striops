/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Self-contained server bundle (.next/standalone/server.js) — binds a plain
  // Node HTTP server on $PORT/$HOSTNAME immediately. Robust on Render free tier.
  output: "standalone",
  // Free-tier / CI: skip lint pass during build (types still checked)
  eslint: { ignoreDuringBuilds: true },
};

export default nextConfig;
